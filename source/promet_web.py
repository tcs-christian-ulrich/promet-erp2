#from inspect import getmembers
import bottle,webapp,logging,promet,threading,time,datetime,sqlalchemy,sqlalchemy.ext.declarative,sqlalchemy.orm.decl_api,hashlib,json
from pkg_resources import require
class Member:
    M_MEMBER = 1           
    M_COLLECTION = 2        
    def __init__(self, name, parent = None):
        self.name = name
        if parent and parent.virname != '':
            self.virname = parent.virname + '/' + name
        else:
            self.virname = name
        self.parent = parent
        self.type = self.M_MEMBER
        if parent:
            parent.append(self)
    def getContent(self,session,request):
        return b''
    def getSize(self,session,request):
        return len(self.getContent(session,request))
    def getProperties(self,session,request):
        p = {}  
        p['displayname'] = self.name
        p['getcontentlength'] = str(self.getSize(session,request))
        if self.type == Member.M_MEMBER:
            p['getcontentlanguage'] = None
            p['getetag'] = hashlib.md5(self.virname.encode()).hexdigest()
        elif Member.M_COLLECTION:
            p['resourcetype'] = '<D:collection/>'
        return p
class Collection(Member):
    COLLECTION_MIME_TYPE = 'application/x-collection'
    def __init__(self, name, parent = None):
        super().__init__(name,parent=parent)
        self.type = Member.M_COLLECTION
    def getMembers(self):
        return []
    def findMember(self,name,session,request):
        for member in self.getMembers(session,request):
            if member.name == name:
                return member
        return None
    def getProperties(self,session,request):
        p = super().getProperties(session,request)
        p['iscollection'] = 1
        p['getcontenttype'] = Collection.COLLECTION_MIME_TYPE
        return p
class StaticCollection(Collection):
    def __init__(self, name, parent=None):
        super().__init__(name, parent=parent)
        self.items = []
    def getMembers(self,session,request):
        return self.items
    def append(self,member):
        self.items.append(member)
def sqlencoder(obj):
    """JSON encoder function for SQLAlchemy special classes."""
    if isinstance(obj, datetime.date):
        return obj.isoformat()
    elif isinstance(obj, decimal.Decimal):
        return float(obj)
class CachedMember(Member):
    def __init__(self, name, parent=None, timeout=3):
        super().__init__(name, parent=parent)
        self.Cached = None
        self.timeout = timeout
    def getContent(self, session, request):
        if not self.Cached or (time.time()>self.Invalid or session != self.CachedSession):
            self.Cached = self.getCachedContent(session,request)
            self.CachedSession = session
            self.Invalid = time.time()+self.timeout
        return self.Cached
class OverviewFile(CachedMember):
    def __init__(self, dataset, format, parent=None):
        super().__init__('list.'+format, parent=parent)
        self.dataset = dataset
    def getCachedContent(self,session,request):
        rows = session.Connection.query(self.dataset).order_by(sqlalchemy.desc(promet.TimestampTable.TimestampD)).limit(100)
        return json.dumps([row for row in rows], cls=sqljson_encoder(), check_circular=False, indent=4).encode()
    def putContent(self,session,request):
        rows = json.load(request.body)
        changed = False
        for row in rows:
            if 'id' in row:
                old_row = session.Connection.query(self.dataset).filter(promet.BasicTable.id==row['id']).first()
                if not old_row:
                    logging.warning('put row not implemented '+row['SQL_ID'])
                else:
                    for field in row:
                        if hasattr(old_row, field):
                            if field not in ['TimestampD','id']:
                                if row[field] != getattr(old_row,field):
                                    setattr(old_row,field,row[field])
                                    #old_row[field] = row[field]
                                    changed = True
        if changed:
            session.Connection.commit()        
    def getProperties(self, session, request):
        res = super().getProperties(session, request)
        res['getcontenttype'] = 'text/x-json'
        return res
class TableCollection(StaticCollection):
    def __init__(self, dataset, parent=None):
        super().__init__(dataset.__tablename__.lower(), parent=parent)
        JsonIndex = OverviewFile(dataset,'json',self)
ExportedTables = [promet.User,promet.Order,promet.Masterdata,promet.PasswordSave]
class PrometSessionElement(webapp.SessionElement):
    def __init__(self) -> None:
        super().__init__()
        self.Connection = None
        self.User = None
        self.LastError = None
        self.root = StaticCollection('')
        def CreateConnection():
            try:
                self.Connection = promet.GetConnection()
                for dataset in promet.Table.metadata.sorted_tables:
                    for table in ExportedTables:
                        if table.__tablename__.lower() == dataset.fullname.lower():
                            TableCollection(table,parent=self.root)
            except BaseException as e:
                self.LastError = e
        self.ConnThread = threading.Thread(target=CreateConnection)
        self.ConnThread.start()
    def FindPath(self,path,session,request):
        elem = self.root
        for e in path:
            tmp = elem.findMember(e,session,request)
            if tmp is None and e[-1:] == '/':
                e = e[:-1] 
                tmp = elem.findMember(e,session,request)
                if tmp and tmp.type == Member.M_MEMBER:
                    tmp = None
            elem = tmp
            if elem == None:
                break
        return (path, elem)
    def WaitforConnection(self):
        for i in range(2000):
            time.sleep(0.1)
            if self.ConnThread and self.ConnThread.is_alive():
                pass
            else:
                if self.LastError:
                    return bottle.error(str(self.LastError))
                if self.Connection:
                    return True
                break
            if self.Connection:
                return True
        return False
    def isAuthorized(self,auth):
        if self.User:
            return True
        if self.WaitforConnection() and auth:
            query = self.Connection.query(promet.User).filter(sqlalchemy.or_(promet.User.Name == auth[0],promet.User.LoginName == auth[0],promet.User.eMail == auth[0])).filter(promet.User.Leaved == None)
            cnt = query.count()
            if cnt == 1:
                self.User = query.first()
                if self.User.checkPassword(auth[1]):
                    self.User.LastLogin = datetime.datetime.now()
                    self.Connection.commit()
                    return True
                else:
                    return False
        return False
def sqljson_encoder(revisit_self = False, fields_to_expand = []):
    _visited_objs = []
    class AlchemyEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, datetime.date):
                return obj.isoformat()
            elif callable(obj) or isinstance(obj,sqlalchemy.orm.decl_api.registry):
                return None
            elif isinstance(obj.__class__, sqlalchemy.ext.declarative.DeclarativeMeta):
                # don't re-visit self
                if revisit_self:
                    if obj in _visited_objs:
                        return None
                    _visited_objs.append(obj)

                # go through each field in this SQLalchemy class
                fields = {}
                for field in [x for x in dir(obj) if not x.startswith('_') and x != 'metadata']:
                    val = obj.__getattribute__(field)
                    # is this field another SQLalchemy object, or a list of SQLalchemy objects?
                    if isinstance(val.__class__, sqlalchemy.ext.declarative.DeclarativeMeta) or (isinstance(val, list) and len(val) > 0 and isinstance(val[0].__class__, sqlalchemy.ext.declarative.DeclarativeMeta)):
                        # unless we're expanding this field, stop here
                        if field not in fields_to_expand:
                            # not expanding this field: set it to None and continue
                            fields[field] = None
                            continue

                    fields[field] = val
                # a json-encodable dict
                return fields
            return json.JSONEncoder.default(self, obj)

    return AlchemyEncoder
webapp.CustomSessionElement(PrometSessionElement)
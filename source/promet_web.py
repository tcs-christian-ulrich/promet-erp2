#from inspect import getmembers
import bottle,webapp,logging,promet,threading,time,datetime,sqlalchemy,hashlib,json
from pkg_resources import require
class Member:
    M_MEMBER = 1           
    M_COLLECTION = 2        
    def __init__(self, name, parent = None):
        self.name = name
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
class OverviewFile(Member):
    def __init__(self, dataset, format, parent=None):
        super().__init__('list.'+format, parent=parent)
        self.dataset = dataset
    def getContent(self,session,request):
        rows = session.Connection.query(self.dataset).limit(100)
        res = json.dumps([dict(row) for row in rows], default=sqlencoder, indent=4)
        return res.encode()
    def getProperties(self, session, request):
        res = super().getProperties(session, request)
        res['getcontenttype'] = 'text/x-json'
        return res
class TableCollection(StaticCollection):
    def __init__(self, dataset, parent=None):
        super().__init__(dataset.fullname.lower(), parent=parent)
        JsonIndex = OverviewFile(dataset,'json',self)
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
                    if dataset.fullname.lower() in ['users','orders','masterdata','pwsave']:
                        TableCollection(dataset,parent=self.root)
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
webapp.CustomSessionElement(PrometSessionElement)
#from inspect import getmembers
import bottle,webapp,logging,promet,threading,time,datetime,sqlalchemy,hashlib
class Member:
    M_MEMBER = 1           
    M_COLLECTION = 2        
    def __init__(self, name, parent = None):
        self.name = name
        self.virname = name
        self.parent = parent
        if parent:
            parent.append(self)
        self.type = Member.M_COLLECTION
    def getProperties(self):
        p = {}  
        p['displayname'] = self.name
        p['getcontentlength'] = '0'
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
    def findMember(self,name):
        for member in self.getMembers():
            if member.name == name:
                return member
        return None
    def getProperties(self):
        p = super().getProperties()
        p['iscollection'] = 1
        p['getcontenttype'] = Collection.COLLECTION_MIME_TYPE
        return p
class StaticCollection(Collection):
    def __init__(self, name, parent=None):
        super().__init__(name, parent=parent)
        self.items = []
    def getMembers(self):
        return self.items
    def append(self,member):
        self.items.append(member)
class PrometSessionElement(webapp.SessionElement):
    def __init__(self) -> None:
        super().__init__()
        self.Connection = None
        self.User = None
        self.LastError = None
        def CreateConnection():
            try:
                self.Connection = promet.GetConnection()
            except BaseException as e:
                self.LastError = e
        self.ConnThread = threading.Thread(target=CreateConnection)
        self.ConnThread.start()
        self.root = StaticCollection('')
    def FindPath(self,path):
        elem = self.root
        for e in path:
            tmp = elem.findMember(e)
            if tmp is None and e[-1:] == '/':
                e = e[:-1] 
                tmp = elem.findMember(e)
                if tmp and tmp.type == promet_web.Member.M_MEMBER:
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
                self.User.LastLogin = datetime.datetime.now()
                self.Connection.commit()
                return True
        return False
webapp.CustomSessionElement(PrometSessionElement)
webapp.ColoredOutput(logging.DEBUG)
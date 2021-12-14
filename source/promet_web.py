import bottle,webapp,logging,promet,threading,time,datetime,sqlalchemy
class Member:
    M_MEMBER = 1           
    M_COLLECTION = 2        
    def getProperties(self):
        return {}  
class Collection(Member):
    def __init__(self, name):
        self.name = name
    def getMembers(self):
        return []
class StaticCollection(Collection):
    def __init__(self, name) -> None:
        Collection(self).__init__(name)
        self.items = []
    def getMembers(self):
        return self.items
root = StaticCollection('')
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
    def WaitforConnection(self):
        for i in range(500):
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
    def is_authorized(self,auth):
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
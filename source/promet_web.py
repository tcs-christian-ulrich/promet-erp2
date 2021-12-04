import webapp,logging,promet,threading,time,datetime
class PrometSessionElement(webapp.SessionElement):
    def __init__(self) -> None:
        super().__init__()
        self.Connection = None
        self.User = None
        def CreateConnection():
            self.Connection = promet.GetConnection()
        threading.Thread(target=CreateConnection).start()
    def WaitforConnection(self):
        for i in range(500):
            if self.Connection:
                return True
            time.sleep(0.1)
        return False
    def is_authorized(self,auth):
        if auth is None: return False
        if self.User:
            return True
        if self.WaitforConnection():
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
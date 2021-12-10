import bottle,webapp,logging,promet,threading,time,datetime
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
        self.ConnThread = threading.Thread(target=CreateConnection).start()
    def WaitforConnection(self):
        for i in range(500):
            if self.ConnThread.is_alive():
                time.sleep(0.1)
            else:
                if self.LastError:
                    return bottle.error(500,str(self.LastError))
                if self.Connection:
                    return True
                break
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
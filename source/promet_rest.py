import threading
import bottle,logging,urllib,os,uuid,webapp,promet,time
from webapp.webapp import SessionElement
ALLOWED_METHODS = ['GET', 'PUT', 'PROPFIND', 'PROPPATCH', 'MKCOL', 'DELETE',
                   'COPY', 'MOVE', 'OPTIONS']
URI_BEGINNING_PATH = {
    'redirection': '/redirect/',
    'authorization': '/login/',
    'system': '/system/',
    'webdav': '/dav/',
    'links': '/'
}
bottle.secret_key = os.urandom(24)
def is_authorized():
    return False
@bottle.get(URI_BEGINNING_PATH['webdav'])
@bottle.get(URI_BEGINNING_PATH['webdav']+'<dataset>')
def list_handler(dataset=None):
    pass
@bottle.get(URI_BEGINNING_PATH['webdav']+'<dataset>/<sql_id>')
def load_handler(dataset,sql_id):
    pass
@bottle.route(URI_BEGINNING_PATH['webdav']+'<dataset>/<sql_id>', method=['PUT', 'POST'])
def save_handler():
    '''Handles name listing'''
    pass
@bottle.delete(URI_BEGINNING_PATH['webdav']+'<dataset>/<sql_id>')
def delete_handler(name):
    '''Handles name deletions'''
    pass
@bottle.hook('before_request')
def before_request():
    """
       * put in g the prepared bottle.response with status and headers
       that can be changed by some methods later
       * allow cross origin for webdav uri that are authorized
       and filter unauthorized bottle.requests!
       * prepare bottle.response to OPTIONS bottle.request on webdav
    """
    if bottle.request.path.startswith(URI_BEGINNING_PATH['webdav']):
        response = None
        bottle.response.headers['Access-Control-Max-Age'] = '3600'
        bottle.response.headers['Access-Control-Allow-Credentials'] = 'true'
        bottle.response.headers['Access-Control-Allow-Headers'] = \
            'Origin, Accept, Accept-Encoding, Content-Length, ' + \
            'Content-Type, Authorization, Depth, If-Modified-Since, '+ \
            'If-None-Match'
        bottle.response.headers['Access-Control-Expose-Headers'] = \
            'Content-Type, Last-Modified, WWW-Authenticate'
        origin = bottle.request.headers.get('Origin')
        bottle.response.headers['Access-Control-Allow-Origin'] = origin
        session = webapp.Session(bottle.request.headers.get('Access-Control-request-Headers'))
        if session.is_authorized(bottle.request.auth):
            status_code = 200
        elif bottle.request.method == 'OPTIONS' and session.sid:
            # tells the world we do CORS when authorized
            bottle.response.headers['Access-Control-request-Headers'] = session.sid
            bottle.response.headers['Access-Control-Allow-Methods'] = ', '.join(ALLOWED_METHODS)
            bottle.response.status = 200
            return
        else:
            bottle.response.headers['WWW-Authenticate'] = 'Basic realm="Promet-ERP"'
            bottle.response.headers['Access-Control-request-Headers'] = session.sid
            bottle.response.status = 401
            return
        bottle.response.status = status_code
class PrometSessionElement(webapp.SessionElement):
    def __init__(self) -> None:
        super().__init__()
        self.Connection = None
        def CreateConnection():
            self.Connection = promet.GetConnection()
        threading.Thread(target=CreateConnection).start()
    def WaitforConnection(self):
        for i in range(500):
            if self.Connection:
                break
            time.sleep(0.1)
    def is_authorized(self,auth):
        self.WaitforConnection()
        return False
webapp.CustomSessionElement(PrometSessionElement)
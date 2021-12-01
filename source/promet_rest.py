import bottle,logging,itsdangerous,urllib,os
ALLOWED_METHODS = ['GET', 'PUT', 'PROPFIND', 'PROPPATCH', 'MKCOL', 'DELETE',
                   'COPY', 'MOVE', 'OPTIONS']
URI_BEGINNING_PATH = {
    'redirection': '/redirect/',
    'authorization': '/login/',
    'system': '/system/',
    'webdav': '/',
    'links': '/'
}
bottle.secret_key = os.urandom(24)
def is_authorized():
    return False
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

        specific_header = bottle.request.headers.get('Access-Control-bottle.request-Headers')

        if is_authorized():
            status_code = 200

        elif bottle.request.method == 'OPTIONS' and specific_header:
            # tells the world we do CORS when authorized
            logging.debug('OPTIONS bottle.request special header: ' + specific_header)
            bottle.response.headers['Access-Control-bottle.request-Headers'] = specific_header
            bottle.response.headers['Access-Control-Allow-Methods'] = ', '.join(ALLOWED_METHODS)
            response = bottle.make_response('', 200, headers)
            return response
        else:
            s = itsdangerous.Signer(bottle.secret_key)
            response.headers['WWW-Authenticate'] = 'Promet login_url=' + \
                urllib.parse.urljoin(bottle.request.url_root,
                URI_BEGINNING_PATH['authorization']) + '?sig=' + \
                s.get_signature(origin) + '{&back_url,origin}'
            response = bottle.make_response('', 401, headers)
            # do not handle the bottle.request if not authorized
            return response
        bottle.response.status = status_code
@bottle.get('/<dataset>')
def list_handler(dataset):
    pass
@bottle.get('/<dataset>/<sql_id>')
def load_handler(dataset,sql_id):
    pass
@bottle.route('/<dataset>/<sql_id>', method=['PUT', 'POST'])
def save_handler():
    '''Handles name listing'''
    pass
@bottle.delete('/<dataset>/<sql_id>')
def delete_handler(name):
    '''Handles name deletions'''
    pass

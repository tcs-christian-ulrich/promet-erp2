import bottle,webapp,logging,webdav
app = bottle.app()
webapp.ColoredOutput(logging.INFO)
@bottle.get('/')
@bottle.get('/index.html')
@bottle.get('/<filepath>')
def get_interface(filepath='/index.html'):
    return ''
webdav.route('/api/v2')
app.run(port=8085)
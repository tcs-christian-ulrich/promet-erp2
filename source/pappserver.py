import bottle
app = bottle.app()
import traceserver.source.prometerp.source.promet_dav as promet_dav
@bottle.get('/')
@bottle.get('/index.html')
@bottle.get('/<filepath>')
def get_interface(filepath='/index.html'):
    return ''
app.run(port=8085)
import bottle
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

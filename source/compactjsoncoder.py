import re,json
def dumps_compact(*sub, **kw):
    non_space_pattern = re.compile('[^ ]')
    compact_length = kw.pop('compact_length', None)
    r = json.dumps(*sub, **kw)
    r = r.replace(']',']\n')
    r = r.replace('[','[\n ')
    r = r.replace('},','},\n')
    return r
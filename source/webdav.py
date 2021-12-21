import sys,urllib,re,urllib.parse,logging
from time import time, timezone, strftime, localtime, gmtime
import os, shutil, uuid, hashlib, mimetypes, base64, bottle,webapp,promet_web
class FileMember(promet_web.Member):
    def __init__(self, name, parent):
        self.name = name
        self.parent = parent
        self.name = name
        self.fsname = parent.fsname + name      # e.g. '/var/www/mysite/some.txt'
        self.virname = parent.virname + name    # e.g. '/mysite/some.txt'
        self.type = Member.M_MEMBER

    def __str__(self):
        return "%s -> %s" % (self.virname, self.fsname)

    def getProperties(self):
        """Return dictionary with WebDAV properties. Values shold be
        formatted according to the WebDAV specs."""
        st = os.stat(self.fsname)
        p = {}
        p['creationdate'] = unixdate2iso8601(st.st_ctime)
        p['getlastmodified'] = unixdate2httpdate(st.st_mtime)
        p['displayname'] = self.name
        p['getetag'] = hashlib.md5(self.fsname).hexdigest()
        if self.type == Member.M_MEMBER:
            p['getcontentlength'] = st.st_size
            p['getcontenttype'], z = mimetypes.guess_type(self.name)
            p['getcontentlanguage'] = None
        else:   # Member.M_COLLECTION
            p['resourcetype'] = '<D:collection/>'
        if self.name[0] == ".":
            p['ishidden'] = 1
        if not os.access(self.fsname, os.W_OK):
            p['isreadonly'] = 1
        if self.name == '/':
            p['isroot'] = 1
        return p

    def sendData(self, wfile,bpoint=0,epoint=0):
        """Send the file to the client. Literally."""
        st = os.stat(self.fsname)
        f = file(self.fsname, 'rb')
        writ = 0
        # for send Range xxx-xxx 
        if bpoint>0 and bpoint<st.st_size:
            f.seek(bpoint)
        if epoint>bpoint:
            if epoint<=st.st_size:
                rsize = epoint - bpoint + 1 
            else:
                rsize = st.st_size - bpoint
        else:
            rsize = st.st_size
        while writ < rsize:
            if (rsize - writ) < 65536:
                buf = f.read(rsize)
            else:
                buf = f.read(65536)
            if not buf:
                break
            writ += len(buf)
            wfile.write(buf)
        f.close()
class DirCollection(FileMember, promet_web.Collection):
    COLLECTION_MIME_TYPE = 'httpd/unix-directory'           # application/x-collection ？
    def __init__(self, fsdir, virdir, parent=None):
        if not os.path.exists(fsdir):
            raise "Local directory (fsdir) not found: " + fsdir
        self.fsname = fsdir
        self.name = virdir
        if self.fsname[-1] != os.sep:
            if self.fsname[-1] == '/': # fixup win/dos/mac separators
                self.fsname = self.fsname[:-1] + os.sep
            else:
                self.fsname += os.sep
        self.virname = virdir
        if self.virname[-1] != '/':
            self.virname += '/'
        self.parent = parent
        self.type = Member.M_COLLECTION

    def getProperties(self):
        p = FileMember.getProperties(self) # inherit file properties
        p['iscollection'] = 1
        p['getcontenttype'] = DirCollection.COLLECTION_MIME_TYPE
        return p

    def getMembers(self):
        """Get immediate members of this collection."""
        l = os.listdir(self.fsname) # obtain a copy of dirlist
        tcount=0
        for tmpi in l:
        		if os.path.isfile(self.fsname+tmpi) == False:
        				l[tcount]=l[tcount]+'/'
        		tcount += 1
        r = []
        for f in l:
            if f[-1] != '/':
                m = FileMember(f, self) # Member is a file
            else:
                m = DirCollection(self.fsname + f, self.virname + f, self) # Member is a collection
            r.append(m)
        return r

		# Return WebDav Root Dir info
    def rootdir(self):
    	return self.fsname
    	
    def findMember(self, name):
        """Search for a particular member."""
        l = os.listdir(self.fsname) # obtain a copy of dirlist
        tcount=0
        for tmpi in l:
            if os.path.isfile(self.fsname+tmpi) == False:
                l[tcount]=l[tcount]+'/'
            tcount += 1
        if name in l:
            if name[-1] != '/':
                return FileMember(name, self)
            else:
                return DirCollection(self.fsname + name, self.virname + name, self)
        elif name[-1] != '/':
            name += '/'
            if name in l:
                return DirCollection(self.fsname + name, self.virname + name, self)

    def sendData(self, wfile):
        """Send "file" to the client. Since this is a directory, build some arbitrary HTML."""
        memb = self.getMembers()
        data = '<html><head><title>%s</title></head><body>' % self.virname
        data += '<table><tr><th>Name</th><th>Size</th><th>Timestamp</th></tr>'
        for m in memb:
            p = m.getProperties()
            if 'getcontentlength' in p:
                p['size'] = int(p['getcontentlength'])
                p['timestamp'] = p['getlastmodified']
            else:
                p['size'] = 0
                p['timestamp'] = '-DIR-'
            data += '<tr><td>%s</td><td>%d</td><td>%s</td></tr>' % (p['displayname'], p['size'], p['timestamp'])
        data += '</table></body></html>'
        wfile.write(data)

    def recvMember(self, rfile, name, size, req):
        """Receive (save) a member file"""
        fname = os.path.join(self.fsname, urllib.unquote(name))
        f = file(fname, 'wb')
        # if size=-1 it's Transfer-Encoding: Chunked mode, like OSX finder using this mode put data
        # so the file size need get here.
        if size == -2:
            l = int(rfile.readline(), 16)
            ltotal = 0
            while l > 0:
                buf = rfile.read(l)
                f.write(buf)        #yield buf
                rfile.readline()
                ltotal += l
                l = int(rfile.readline(), 16)
        elif size > 0:      # if size=0 ,just save a empty file.
            writ = 0
            bs = 65536
            while True:
                if size != -1 and (bs > size-writ):
                    bs = size-writ
                buf = rfile.read(bs)
                if len(buf) == 0:
                    break
                f.write(buf)
                writ += len(buf)
                if size != -1 and writ >= size:
                    break
        f.close()
def unixdate2iso8601(d):
    tz = timezone / 3600 # can it be fractional?
    tz = '%+03d' % tz
    return strftime('%Y-%m-%dT%H:%M:%S', localtime(d)) + tz + ':00'
def unixdate2httpdate(d):
    return strftime('%a, %d %b %Y %H:%M:%S GMT', gmtime(d))
class Tag:
    def __init__(self, name, attrs, data='', parser=None):
        self.d = {}
        self.name = name
        self.attrs = attrs
        if type(self.attrs) == type(''):
            self.attrs = splitattrs(self.attrs)
        for a in self.attrs:
            if a.startswith('xmlns'):
                nsname = a[6:]
                parser.namespaces[nsname] = self.attrs[a]
        self.rawname = self.name

        p = name.find(':')
        if p > 0:
            nsname = name[0:p]
            if nsname in parser.namespaces:
                self.ns = parser.namespaces[nsname]
                self.name = self.rawname[p+1:]
        else:
            self.ns = ''
        self.data = data

    # Emulate dictionary d
    def __len__(self):
        return len(self.d)

    def __getitem__(self, key):
        return self.d[key]

    def __setitem__(self, key, value):
        self.d[key] = value

    def __delitem__(self, key):
        del self.d[key]

    def __iter__(self):
        return self.d.__iter__()

    def __contains__(self, key):
        return key in self.d

    def __str__(self):
        """Returns unicode semi human-readable representation of the structure"""
        if self.attrs:
            s = u'<%s %s> %s ' % (self.name, self.attrs, self.data)
        else:
            s = u'<%s> %s ' % (self.name, self.data)

        for k in self.d:
            if type(self.d[k]) == type(self):
                s += u'|%s: %s|' % (k, str(self.d[k]))
            else:
                s += u'|' + u','.join([str(x) for x in self.d[k]]) + u'|'
        return s

    def addChild(self, tag):
        """Adds a child to self. tag must be instance of Tag"""
        if tag.name in self.d:
            if type(self.d[tag.name]) == type(self): # If there are multiple sibiling tags with same name, form a list :)
                self.d[tag.name] = [self.d[tag.name]]
            self.d[tag.name].append(tag)
        else:
            self.d[tag.name] = tag
        return tag
class XMLDict_Parser:
    def __init__(self, xml):
        self.xml = xml
        self.p = 0
        self.encoding = sys.getdefaultencoding()
        self.namespaces = {}

    def getnexttag(self):
        ptag = self.xml.find('<', self.p)
        if ptag < 0:
            return None, None, self.xml[self.p:].strip()
        data = self.xml[self.p:ptag].strip()
        self.p = ptag
        self.tagbegin = ptag
        p2 = self.xml.find('>', self.p+1)
        if p2 < 0:
            raise "Malformed XML - unclosed tag?"
        tag = self.xml[ptag+1:p2]
        self.p = p2+1
        self.tagend = p2+1
        ps = tag.find(' ')
        ### Change By LCJ @ 2017/9/7 from  [ if ps > 0: ]  ###
        ### for IOS Coda Webdav support ###
        if ps > 0 and tag[-1] != '/':
            tag, attrs = tag.split(' ', 1)
        else:
            attrs = ''
        return tag, attrs, data

    def builddict(self):
        """Builds a nested-dictionary-like structure from the xml. This method
        picks up tags on the main level and calls processTag() for nested tags."""
        d = Tag('<root>', '')
        while True:
            tag, attrs, data = self.getnexttag()
            if data != '': # data is actually that between the last tag and this one
                sys.stderr.write("Warning: inline data between tags?!\n")
            if not tag:
                break
            if tag[-1] == '/': # an 'empty' tag (e.g. <empty/>)
                d.addChild(Tag(tag[:-1], attrs, parser=self))
                continue
            elif tag[0] == '?': # special tag
                t = d.addChild(Tag(tag, attrs, parser=self))
                if tag == '?xml' and 'encoding' in t.attrs:
                    self.encoding = t.attrs['encoding']
            else:
                try:
                    self.processTag(d.addChild(Tag(tag, attrs, parser=self)))
                except:
                    sys.stderr.write("Error processing tag %s\n" % tag)
        d.encoding = self.encoding
        return d

    def processTag(self, dtag):
        """Process single tag's data"""
        until = '/'+dtag.rawname
        while True:
            tag, attrs, data = self.getnexttag()
            if data:
                dtag.data += data
            if tag == None:
                sys.stderr.write("Unterminated tag '"+dtag.rawname+"'?\n")
                break
            if tag == until:
                break
            if tag[-1] == '/':
                dtag.addChild(Tag(tag[:-1], attrs, parser=self))
                continue
            self.processTag(dtag.addChild(Tag(tag, attrs, parser=self)))
def splitattrs(att):
    """Extracts name="value" pairs from string; returns them as dictionary"""
    d = {}
    for m in re.findall('([a-zA-Z_][a-zA-Z_:0-9]*?)="(.+?)"', att):
        d[m[0]] = m[1]
    return d
def builddict(xml):
    """Wrapper function for straightforward parsing"""
    p = XMLDict_Parser(xml)
    return p.builddict()
def split_path(path):
    if path.startswith(dav_root):
        path = path[len(dav_root):]
    #Splits path string in form '/dir1/dir2/file' into parts
    p = path.split('/')[1:]
    while p and p[-1] in ('','/'):
        p = p[:-1]
        if len(p) > 0:
            p[-1] += '/'
    return p
def serverpath(path):
    #return bottle.request.url[:bottle.request.url.find(dav_root)]+
    return dav_root+'/'+path
app = bottle.app()
dav_root = '/api/v2'
a_all_props =   ['name', 'parentname', 'href', 'ishidden', 'isreadonly', 'getcontenttype',
                 'contentclass', 'getcontentlanguage', 'creationdate', 'lastaccessed', 'getlastmodified',
                 'getcontentlength', 'iscollection', 'isstructureddocument', 'defaultdocument',
                 'displayname', 'isroot', 'resourcetype']
a_basic_props = ['name', 'getcontenttype', 'getcontentlength', 'creationdate', 'iscollection', 'resourcetype']
@bottle.error(405)
def method_not_allowed(old_res):
    if bottle.request.method == 'OPTIONS':
        res = bottle.HTTPResponse()
        handle_headers(res)
        return res
    elif bottle.request.method == 'PROPFIND':
        res = bottle.HTTPResponse()
        session = handle_headers(res)
        if res.status_code == 200 and not session.User:
            res.status = 403
            return res
        elif res.status_code != 200:
            return res
        depth = 'infinity'
        if 'Depth' in bottle.request.headers:
            depth = bottle.request.headers['Depth'].lower()
        d = builddict(bottle.request.body.read().decode())
        wished_all = False
        if len(d) == 0:
            wished_props = a_basic_props
        else:
            if 'allprop' in d['propfind']:
                wished_props = a_all_props
                wished_all = True
            else:
                wished_props = []
                pd = d['propfind']['prop']
                for prop in pd:
                     wished_props.append(prop.split(' ')[0])
        path, elem = session.FindPath(split_path(bottle.request.path),session,bottle.request)
        if not elem:
            if len(path) >= 1: # it's a non-existing file
                res.status = 404
                return res
            else:
                elem = promet_web.root 
        if depth != '0' and not elem:   #or elem.type != Member.M_COLLECTION:
            res.status = 406
            return res
        res.status = 207
        res.headers['Content-Type'] = 'text/xml'
        res.headers['charset'] = '"utf-8"'
        res.body += '<?xml version="1.0" encoding="utf-8" ?>\n'
        res.body += '<D:multistatus xmlns:D="DAV:" xmlns:Z="urn:schemas-microsoft-com:">\n'

        def write_props_member(m):
            res.body += '<D:response>\n<D:href>%s</D:href>\n' % (serverpath(urllib.parse.quote(m.virname)))     #add urllib.quote for chinese
            props = m.getProperties(session,bottle.request)       # get the file or dir props 
            # 200
            res.body += '<D:propstat>\n<D:prop>\n'
            # For OSX Finder : getlastmodified,getcontentlength,resourceType
            if ('quota-available-bytes' in wished_props) or ('quota-used-bytes'in wished_props) or ('quota' in wished_props) or ('quotaused'in wished_props):
                sDisk = os.statvfs('.')
                props['quota-used-bytes'] = (sDisk.f_blocks - sDisk.f_bavail) * sDisk.f_frsize
                props['quotaused'] = (sDisk.f_blocks - sDisk.f_bavail) * sDisk.f_frsize
                props['quota-available-bytes'] = sDisk.f_bavail * sDisk.f_frsize
                props['quota'] = sDisk.f_bavail * sDisk.f_frsize                                
            for wp in wished_props:
                if wp in props:
                    res.body += '  <D:%s>%s</D:%s>\n' % (wp, str(props[wp]), wp)
            res.body += '</D:prop>\n<D:status>HTTP/1.1 200 OK</D:status>\n</D:propstat>\n'
            # 404
            res.body += '<D:propstat>\n<D:prop>\n'
            for wp in wished_props:
                if not wp in props:
                    res.body += '  <D:%s/>\n' % wp
            res.body += '</D:prop>\n<D:status>HTTP/1.1 404 Not Found</D:status>\n</D:propstat>\n'
            res.body += '</D:response>\n'
        adepth = 0
        if depth == 'infinity':
            depth = 999999
        else:
            depth = int(depth)
        actElements = [elem]
        while (adepth <= depth) and len(actElements)>0:
            newElements = []
            for elem in actElements:
                if elem.type == promet_web.Collection.M_COLLECTION:
                    for m in elem.getMembers(session,bottle.request):
                        newElements.append(m)
                write_props_member(elem)
            actElements = newElements
            adepth += 1
        res.body += '</D:multistatus>'
        #logging.debug(bottle.request.body.read().decode())
        #logging.debug(res.body)
        return res
    return bottle.request.app.default_error_handler(old_res)
def handle_headers(response):
    response.set_header('Access-Control-Allow-Origin', '*')
    response.headers['Allow'] = str(dav_methods)[2:-2].replace('\'','')
    response.headers['DAV']   = '1, 2'    #OSX Finder need Ver 2, if Ver 1 -- read only
    response.headers['MS-Author-Via'] = 'DAV'
    response.headers['Access-Control-Max-Age'] = '3600'
    response.headers['Access-Control-Allow-Credentials'] = 'true'
    response.headers['Access-Control-Allow-Headers'] = \
        'Origin, Accept, Accept-Encoding, Content-Length, ' + \
        'Content-Type, Authorization, Depth, If-Modified-Since, '+ \
        'If-None-Match'
    response.headers['Access-Control-Expose-Headers'] = \
        'Content-Type, Last-Modified, WWW-Authenticate'
    origin = bottle.request.headers.get('Origin')
    response.headers['Access-Control-Allow-Origin'] = origin
    session = webapp.Session(origin)
    if session.isAuthorized(bottle.request.auth):
        response.status = 200
        response.headers['Access-Control-request-Headers'] = session.sid
    elif bottle.request.method == 'OPTIONS' and session.sid:
        # tells the world we do CORS when authorized
        response.headers['Access-Control-request-Headers'] = session.sid
        response.status = 200
    elif session.Connection is not None:
        response.headers['WWW-Authenticate'] = 'Basic realm="Promet-ERP"'
        response.headers['Access-Control-request-Headers'] = session.sid
        response.status = 401
    return session
dav_methods = ['OPTIONS', 'PROPFIND', 'GET', 'HEAD', 'POST', 'DELETE', 'PUT', 'COPY', 'MOVE', 'LOCK', 'UNLOCK', 'PROPPATCH', 'MKCOL']
def route(root):
    dav_root = root
    @bottle.route(dav_root+'<:re:.*>', methods=dav_methods)
    def dav_query():
        p = bottle.request.path
        if p.startswith('v2'):
            p = p[2:]
        if bottle.request.method in ['GET','HEAD']:
            res = bottle.response
            session = handle_headers(res)
            if res.status_code == 200 and not session.User:
                res.status = 403
                return res
            elif res.status_code != 200:
                return res
        else:
            return None
"""
class DAVRequestHandler(BaseHTTPRequestHandler):
    def do_DELETE(self):
        if self.WebAuth():
            return         
        path = urllib.unquote(self.path)
        if path == '':
            self.send_error(404, 'Object not found')
            self.send_header('Content-length', '0')
            self.end_headers()
            return
        path = self.server.root.rootdir() + path
        if os.path.isfile(path):
            os.remove(path)         #delete file
        elif os.path.isdir(path):
            shutil.rmtree(path)     #delete dir
        else:
            self.send_response(404,'Not Found')
            self.send_header('Content-length', '0')
            self.end_headers()
            return
        self.send_response(204, 'No Content')
        self.send_header('Content-length', '0')
        self.end_headers()
        
    def do_MKCOL(self):
        if self.WebAuth():
            return 
        path = urllib.unquote(self.path)
        if path != '':
            path = self.server.root.rootdir() + path
            if os.path.isdir(path) == False:
                os.mkdir(path)
                self.send_response(201, "Created")
                self.send_header('Content-length', '0')
                self.end_headers()
                return
        self.send_response(403, "OK")
        self.send_header('Content-length', '0')
        self.end_headers()        

    def do_MOVE(self):
        if self.WebAuth():
            return 
        oldfile = self.server.root.rootdir() + urllib.unquote(self.path)
        newfile = self.server.root.rootdir() + urlparse.urlparse(urllib.unquote(self.headers['Destination'])).path         
        if (os.path.isfile(oldfile)==True and os.path.isfile(newfile)==False): 
            shutil.move(oldfile,newfile)
        if (os.path.isdir(oldfile)==True and os.path.isdir(newfile)==False):
            os.rename(oldfile,newfile)
        self.send_response(201, "Created")
        self.send_header('Content-length', '0')
        self.end_headers()        

    def do_COPY(self):
        if self.WebAuth():
            return 
        oldfile = self.server.root.rootdir() + urllib.unquote(self.path)
        newfile = self.server.root.rootdir() + urlparse.urlparse(urllib.unquote(self.headers['Destination'])).path 
        if (os.path.isfile(oldfile)==True):        #  and os.path.isfile(newfile)==False):  copy can rewrite.
            shutil.copyfile(oldfile,newfile)
        self.send_response(201, "Created")
        self.send_header('Content-length', '0')
        self.end_headers()

    def do_LOCK(self):
        if 'Content-length' in self.headers:
            req = self.rfile.read(int(self.headers['Content-length']))
        else:
            req = self.rfile.read()
        d = builddict(req)
        clientid = str(d['lockinfo']['owner']['href'])[7:]      # temp: need Change other method!!!
        lockid = str(uuid.uuid1())        
        retstr = '<?xml version="1.0" encoding="utf-8" ?>\n<D:prop xmlns:D="DAV:">\n<D:lockdiscovery>\n<D:activelock>\n<D:locktype><D:write/></D:locktype>\n<D:lockscope><D:exclusive/></D:lockscope>\n<D:depth>Infinity</D:depth>\n<D:owner>\n<D:href>'+clientid+'</D:href>\n</D:owner>\n<D:timeout>Infinite</D:timeout>\n<D:locktoken><D:href>opaquelocktoken:'+lockid+'</D:href></D:locktoken>\n</D:activelock>\n</D:lockdiscovery>\n</D:prop>\n'
        self.send_response(201,'Created')
        self.send_header("Content-type",'text/xml')
        self.send_header("charset",'"utf-8"')
        self.send_header("Lock-Token",'<opaquelocktoken:'+lockid+'>')
        self.send_header('Content-Length',len(retstr))
        self.end_headers()
        self.wfile.write(retstr)
        self.wfile.flush()

    def do_UNLOCK(self):
        # frome self.headers get Lock-Token: 
        self.send_response(204, 'No Content')        # unlock using 204 for sucess.
        self.send_header('Content-length', '0')
        self.end_headers()

    def do_GET(self, onlyhead=False):
        if self.WebAuth():
            return 
        path, elem = self.path_elem()
        if not elem:
            self.send_error(404, 'Object not found')
            return
        try:
            props = elem.getProperties()
        except:
            self.send_response(500, "Error retrieving properties")
            self.end_headers()
            return
        # when the client had Range: bytes=3156-3681 
        bpoint = 0
        epoint = 0
        fullen = props['getcontentlength']
        if 'Range' in self.headers:
            stmp = self.headers['Range'][6:]
            stmp = stmp.split('-')
            try:
                bpoint = int(stmp[0])
            except:
                bpoint = 0
            try:
                epoint = int(stmp[1])
            except:
                epoint = fullen - 1
            if (epoint<=bpoint):
                bpoint = 0
                epoint = fullen - 1
            fullen = epoint - bpoint + 1
        if epoint>0:
            self.send_response(206, 'Partial Content')            
            self.send_header("Content-Range", " Bytes %s-%s/%s" % (bpoint, epoint, fullen))            
        else:
            self.send_response(200, 'OK')
        if elem.type == Member.M_MEMBER:
            self.send_header("Content-type", props['getcontenttype'])
            self.send_header("Last-modified", props['getlastmodified'])
            self.send_header("Content-length", fullen)
        else:
            try:
                ctype = props['getcontenttype']
            except:
                ctype = DirCollection.COLLECTION_MIME_TYPE
            self.send_header("Content-type", ctype)
        self.end_headers()
        if not onlyhead:
            if fullen >0 :      # all 0 size file don't need this 
                elem.sendData(self.wfile,bpoint,epoint)

    def do_HEAD(self):
        self.do_GET(True)           # HEAD should behave like GET, only without contents

    def do_PUT(self):
        if self.WebAuth():
            return 
        try:
            if 'Content-length' in self.headers:
                size = int(self.headers['Content-length'])
            elif 'Transfer-Encoding' in self.headers:
                if self.headers['Transfer-Encoding'].lower()=='chunked':
                    size = -2
            else:
                size = -1
            path, elem = self.path_elem_prev()
            ename = path[-1]
        except:
            self.send_response(400, 'Cannot parse request')
            self.send_header('Content-length', '0')
            self.end_headers()
            return
        # for OSX finder, it's first send a 0 byte file,and you need response a 201 code,and then osx send real file.
        # OSX finder don't using content-length.
        if ename == '.DS_Store':
            self.send_response(403, 'Forbidden')
            self.send_header('Content-length', '0')
            self.end_headers()
        else:
            try:
                elem.recvMember(self.rfile, ename, size, self)
            except:
                self.send_response(500, 'Cannot save file')
                self.send_header('Content-length', '0')
                self.end_headers()
                return
            if size == 0:
                self.send_response(201, 'Created')
            else:
                self.send_response(200, 'OK')
            self.send_header('Content-length', '0')
            self.end_headers()

    def split_path(self, path):
        #Splits path string in form '/dir1/dir2/file' into parts
        p = path.split('/')[1:]
        while p and p[-1] in ('','/'):
           p = p[:-1]
           if len(p) > 0:
              p[-1] += '/'
        return p

    def path_elem(self):
        #Returns split path (see split_path()) and Member object of the last element
        path = self.split_path(urllib.unquote(self.path))
        elem = self.server.root
        for e in path:
            elem = elem.findMember(e)
            if elem == None:
                break
        return (path, elem)

    def path_elem_prev(self):
        #Returns split path (see split_path()) and Member object of the next-to-last element
        path = self.split_path(urllib.unquote(self.path))
        elem = self.server.root
        for e in path[:-1]:
            elem = elem.findMember(e)
            if elem == None:
                break
        return (path, elem)
     
     # disable log info output to screen    
    def log_message(self,format,*args):
    	pass
"""
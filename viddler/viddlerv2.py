# Viddler V2 Python API
# Todd Troxell <todd@viddler.com>
#
# Copyright 2011 Todd Troxell
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import pycurl
import simplejson
from StringIO import StringIO
from  urllib import urlencode

DEBUG = False
# viddler endpoint
API_URL="http://api.viddler.com/api/v2/"

class ViddlerV2(object):
    def __init__(self, api_key, endpoint=API_URL, debug=DEBUG, session_id=None):
        self.api_key = api_key
        self.endpoint = API_URL
        self.debug = debug
        self.session_id = session_id

    def auth(self, username, passwd):
        data = self.get('viddler.users.auth', {"user": username,
                                               "password": passwd})
        self.session_id = data['auth']['sessionid']
        if self.debug:
            print "got session id: %s" % (self.session_id)
        return self.session_id

    def _rpc(self, args={}):
        c = pycurl.Curl()
        
        if self.session_id:
            args['sessionid'] = self.session_id
        if self.api_key:
            args['api_key'] = self.api_key
            
        urlparams = urlencode(args)
        
        if args['http_method'] == 'GET':

            url =  self.endpoint + args['method'] + ".json?" + urlparams
        elif args['http_method'] == 'POST':
            c.setopt(c.POST, 1)
            c.setopt(c.POSTFIELDS, urlparams)
            url =  self.endpoint + args['method'] + ".json"
        else:
            raise InvalidMethod(args['http_method'])
        
        if self.debug:
            print url
        c.setopt(c.URL, url)
        buf = StringIO()

        
        #CURLOPT_CONNECTTIMEOUT => 10
        
        if self.debug:
            c.setopt(c.VERBOSE, 1)
            
        c.setopt(c.WRITEFUNCTION, buf.write)
        c.perform()
        c.close()
        buf.seek(0)
        #data = buf.read()
        data = simplejson.load(buf)
        return data
    
    def _pycurl_upload(self, params, filepath, progress_func):
        c = pycurl.Curl()
        del params['file']
        endpoint = params['endpoint']
        del params['endpoint']

        for key in params:
            params[key] = params[key].encode('UTF-8')

        if self.session_id:
            params['sessionid'] = self.session_id
        if self.api_key:
            params['api_key'] = self.api_key

        curlpost = params.items()
        curlpost.append(("file", (c.FORM_FILE, filepath.encode())))
        if DEBUG:
            print curlpost
        out = StringIO()
        c.setopt(c.POST, 1)
        c.setopt(c.URL, endpoint)
        c.setopt(c.HTTPPOST, curlpost)
        if DEBUG:
            c.setopt(c.VERBOSE, 1)
        if progress_func:
            c.setopt(c.PROGRESSFUNCTION, progress_func)
            c.setopt(c.NOPROGRESS, 0)
        c.setopt(pycurl.WRITEFUNCTION, out.write)
        c.perform()
        c.close()
        out.seek(0)
        data = simplejson.load(out)
        return data
    
    
    def get(self, method, args={}):
        args['http_method'] = "GET"
        args['method'] = method
        return self._rpc(args)
    
    def post(self, method, args={}):
        args['http_method'] = 'POST'
        args['method'] = method
        return self._rpc(args)
        
    def upload(self, path, args={}, progress_func=None):
        fh = open(path, 'r')
        print self.get('viddler.videos.prepareUpload')
        args['file'] = fh
        args['endpoint'] = self.get('viddler.videos.prepareUpload')['upload']['endpoint']

        args['http_method'] = 'POST'
        ret = self._pycurl_upload(args, path, progress_func)
        fh.close()
        return ret
    

    def test_echo(self):
        print self.get("echo")


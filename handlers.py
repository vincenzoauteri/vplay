import os 
from google.appengine.ext import db
import webapp2
import re
import cgi
from security import *
import jinja2
import logging
from mail import *
import urllib


from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers

jinja_env = jinja2.Environment(
        autoescape=True, loader = jinja2.FileSystemLoader(
            os.path.join(os.path.dirname(__file__), 'templates')))


#General 
def render_str(template, **params):
    """Function that render a jinja template with string substitution"""
    t = jinja_env.get_template(template)
    return t.render(params)

class Handler(webapp2.RequestHandler):
    """General class to render http response"""

    def write(self, *a, **kw):
        """Write generic http response with the passed parameters"""
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        """Utility function that can add new stuff to parameters passed"""
        params['style']='cerulean'
        if self.user : 
          params['welcome']='%s' % self.user.username
          params['logout']='Logout'
        else :
          params['welcome']='Login'
          params['login']='Login'
          params['signup']='Signup'

        return render_str(template, **params)

    def render(self, template, **kw):         
        """Render jinja template with named parameters"""
        self.write(self.render_str(template, **kw))
    
    def set_secure_cookie(self, name, val):
        """Send a http header with a hashed cookie"""
        hashed_cookie = make_cookie_hash(val)
        self.response.headers.add_header('Set-Cookie',
              "%s=%s; Path='/'" % (name,hashed_cookie))

    def read_secure_cookie(self, name):
        """Check if requesting browser sent us a cookie"""
        hashed_cookie = self.request.cookies.get(name)
        logging.error("Cookie name %s hash %s" % (name,hashed_cookie)) 
        if hashed_cookie :
            return verify_cookie_hash(hashed_cookie)
        else:
            return None

    def initialize(self, *a, **kw):
        """Function called before requests are processed.
           Used to check for sent cookies"""
        webapp2.RequestHandler.initialize(self, *a, **kw)
        uid = self.read_secure_cookie('user_id')
        self.user = uid and User.get_by_id(int(uid))




class VideoHandler(Handler):

    def render_front(self, entries={}):
        self.render('sintel.html')

    def get(self):
        self.render_front()

class YoutubeHandler(Handler):

    def render_front(self, entries={}):
        self.render('youtube.html')

    def get(self):
        self.render_front()

class VideoListHandler(Handler):

    def render_front(self, entries={}):
        """utility function used to render the front page"""
        path= os.path.join(os.path.dirname(__file__),'list')
        self.render('list.html',file_list=os.listdir(path))

    def get(self):
        """function called when the front page is requested"""
        self.render_front()

        """
    def get(self):
      path= os.path.join(os.path.dirname(__file__),'list')

"""

class FrontPageHandler(Handler):
    """Class used to render the main page of the site"""

    def render_front(self, entries={}):
        """utility function used to render the front page"""
        self.render('index.html')

    def get(self):
        """function called when the front page is requested"""
        self.render_front()

class BlobHandler(Handler):
    def get(self):
        blobs = [blob.key() for blob in blobstore.BlobInfo.all()]
        names = [blob.filename for blob in blobstore.BlobInfo.all()]
        tup = zip(blobs,names)
        upload_url = blobstore.create_upload_url('/upload')
        self.render('blob.html',blobs=tup,upload_url=upload_url);
#        self.response.out.write('<html><body>')
#        self.response.out.write('<form action="%s" method="POST" enctype="multipart/form-data">' % upload_url)
#        self.response.out.write("""Upload File: <input type="file" name="file"><br> <input type="submit"
#               name="submit" value="Submit"> </form></body></html>""")

class UploadHandler(blobstore_handlers.BlobstoreUploadHandler):
    def post(self):
       upload_files = self.get_uploads('file')  # 'file' is file upload field in the form
       blob_info = upload_files[0]
       self.redirect('/serve/%s' % blob_info.key())

class ServeHandler(blobstore_handlers.BlobstoreDownloadHandler):
    def get(self, resource):
      resource = str(urllib.unquote(resource))
      blob_info = blobstore.BlobInfo.get(resource)
      self.response.headers["Content-Type"] = "video/mp4"
      logging.error(self.response.headers)
      self.send_blob(blob_info)



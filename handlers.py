import os 
from google.appengine.ext import db
import webapp2
import re
import cgi
from security import *
import jinja2
import logging
import urllib


from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.ext import ndb


jinja_env = jinja2.Environment(
        autoescape=True, loader = jinja2.FileSystemLoader(
            os.path.join(os.path.dirname(__file__), 'templates')))

class Video(ndb.Model):
    """Models an individual Guestbook entry with content and date."""
    name = ndb.StringProperty()
    blob= ndb.StringProperty()

    @classmethod
    def query_blob(cls, ancestor_key):
      return cls.query(ancestor=ancestor_key).order(-cls.name)

def init_db():
    ancestor_key = ndb.Key("Videos","VideoKey");
    #videos_entity = ancestor_key.get();
    results = Video.query(ancestor=ancestor_key).order(-Video.name).fetch(20)
    video = Video(parent=ancestor_key,name="test",blob="test")
    video.put()

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
        self.render('list.html',file_list=os.listdir('videos'))

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
        #self.render('index.html')
        self.redirect('/library')

    def get(self):
        """function called when the front page is requested"""
        self.render_front()

class BlobHandler(Handler):
    def get(self):
        upload_url = blobstore.create_upload_url('/upload')
        error = self.request.get("error")
        logging.error(error)
        error_desc=""
        if error=="noname":
            error_desc = "Upload file must have a name"
        elif error=="nofile":
            error_desc = "Error uploading file"

        self.render('blob.html',error=error_desc,upload_url=upload_url);

class VideoLibraryHandler(Handler):
    def get(self):
        ancestor_key = ndb.Key("Videos","VideoKey");
        results = Video.query(ancestor=ancestor_key).order(Video.name).fetch(20)
        tup = list()
        for result in results:
            tup.append((result.name,result.blob))
        self.render('library.html',videos=tup);

class DeleteVideoHandler(Handler):
    def get(self):
        ancestor_key = ndb.Key("Videos","VideoKey");
        results = Video.query(ancestor=ancestor_key).order(Video.name).fetch(20)
        tup = list()
        for result in results:
            tup.append((result.name,result.blob))
        self.render('delete.html',videos=tup);

class UploadHandler(blobstore_handlers.BlobstoreUploadHandler):
    def post(self):
       ancestor_key = ndb.Key("Videos","VideoKey");
       video_name = self.request.get("name")
       upload_files = self.get_uploads('file')  # 'file' is file upload field in the form
       if video_name and upload_files:
            blob_info = upload_files[0]
            video = Video(parent=ancestor_key,name=video_name,blob=str(blob_info.key()))
            if video:
                video.put()
                self.redirect('/library')
       elif not video_name :
           error="noname"
           self.redirect('/blob?error='+error);
       elif not upload_files:
           error="nofile"
           self.redirect('/blob?error='+error);

class ServeHandler(blobstore_handlers.BlobstoreDownloadHandler):
    def get(self, resource):
      resource = str(urllib.unquote(resource))
      blob_info = blobstore.BlobInfo.get(resource)
      self.response.headers["Content-Type"] = "video/mp4"
      logging.error(self.response.headers)
      self.send_blob(blob_info)

class TestHandler(Handler):
    def get(self):
      self.render("test.html")



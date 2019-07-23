import webapp2
import jinja2
import os
import datetime
from google.appengine.ext import ndb
import geocoder
import uuid
#from folder import file:

class User(ndb.Model): #traits is an array that's filled from the personal quiz
     username=ndb.StringProperty(required=True)
     password=ndb.StringProperty(required=True)
     email=ndb.StringProperty(required=True)
     traits=ndb.FloatProperty(required=True, repeated=True)
     id=str(uuid.uuid4())

jinja_env=jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    undefined=jinja2.StrictUndefined, #catches template errors
    autoescape=True
)
#To run the code: dev_appserver.py app.yaml
# control+c to end process
#handler section
class AboutPage(webapp2.RequestHandler): #get, post
    def get(self):
        #self.response.headers['Content-Type']="text/html" #text/plain
        about_template=jinja_env.get_template('/templates/about.html')#load up the about page and access quotes api
        url="https://api.forismatic.com/api/1.0/?method=getQuote&format=json&lang=en" #FORISMATIC API gets random quote
        response=urlfetch.fetch(url)
        content=response.content
        qdata=json.loads(content)
        # returns {"quoteText":"Love is not blind; it simply enables one to see things others fail to see.", "quoteAuthor":"", "senderName":"", "senderLink":"", "quoteLink":"http://forismatic.com/en/848e15db47/"}
        quote=""
        if qdata["quoteAuthor"]=="":
            quote=qdata["quoteText"]
        else:
            quote=qdata["quoteText"]+" - "+ qdata["quoteAuthor"]
        q={"quote":quote}
        self.response.write(welcome_template.render(q))#add the form
    def post(self): #link to another web page
        self.redirect('/login')

class LoginPage(webapp2.RequestHandler): #get, post
    def get(self):
        #self.response.headers['Content-Type']="text/html" #text/plain
        user=users.get_current_user()
        login_template=jinja_env.get_template('/templates/login.html')#load up the about page and access quotes api
        self.response.write(welcome_template.render())#add the form
    def post(self): #link to another web page
        pass

#the app configuration
app=webapp2.WSGIApplication([ #about, login, create account, mood, daily recommendations, food, physical+leisure,
#social events, attractions
    ('/', AboutPage), ('/login', LoginPage),
], debug=True)  #array is all the routes in application (like home, about page)

import webapp2
import jinja2
import os
import datetime
from google.appengine.ext import ndb
from google.appengine.api import urlfetch
import uuid
import urllib2
import json
#from folder import file:

currUser=None
class User(ndb.Model): #traits is an array that's filled from the personal quiz
     username=ndb.StringProperty(required=True)
     password=ndb.StringProperty(required=True)
     email=ndb.StringProperty(required=True)
     traits=ndb.FloatProperty(repeated=True)
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
        about_template=jinja_env.get_template('/about.html')#load up the about page and access quotes api
        url="https://api.forismatic.com/api/1.0/?method=getQuote&format=json&lang=en" #FORISMATIC API gets random quote
        response=urlfetch.fetch(url)
        content=response.content
        qdata=json.loads(content)
        # returns {"quoteText":"Love is not blind; it simply enables one to see things others fail to see.", "quoteAuthor":"", "senderName":"", "senderLink":"", "quoteLink":"http://forismatic.com/en/848e15db47/"}
        quote=""
        author=""
        if qdata["quoteAuthor"]=="":
            quote=qdata["quoteText"]
        else:
            quote=qdata["quoteText"]
            author=" - "+ qdata["quoteAuthor"]
        q={"quote":quote, "author":author}
        self.response.write(about_template.render(q))#add the form
    def post(self): #link to another web page
        self.redirect('/login')

class LoginPage(webapp2.RequestHandler):
    def get(self):
        login_template=jinja_env.get_template('/login.html')
        self.response.write(login_template.render())#add the form
    def post(self): #link to another web page
        u=self.request.get("username")
        p=self.request.get("password")
        data=User.query().fetch() #does data return none if empty?
        if data==None: #if no one's made an account
            self.redirect('/createaccount')
        else:
            for d in data:
                if d.username==u and d.password==p:
                    self.redirect('/mood')

class AccountPage(webapp2.RequestHandler): #get, post
    def get(self):
        account_template=jinja_env.get_template('/account.html')
        self.response.write(account_template.render())
    def post(self): #link to another web page
        user=User(username=u, password=p, email=e)
        user.put()

class MoodPage(webapp2.RequestHandler): #get, post
    def get(self):
        mood_template=jinja_env.get_template('/templates/mood.html')
        self.response.write(account_template.render())
    def post(self): #link to another web page
        pass
#the app configuration
app=webapp2.WSGIApplication([ #about, login, create account, mood, daily recommendations, food, physical+leisure,
#social events, attractions
    ('/', AboutPage), ('/login', LoginPage), ('/createaccount', AccountPage), ('/mood', MoodPage),
], debug=True)  #array is all the routes in application (like home, about page)

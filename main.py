import webapp2
import jinja2
import os
import datetime
from google.appengine.ext import ndb
from google.appengine.api import urlfetch
from google.appengine.api import users
from time import ctime
import uuid
import urllib2
import json
import random
#AIzaSyAqJGmC3v_P3lGDO-qILr-XA0m4axi3oY8
apikey="AIzaSyAqJGmC3v_P3lGDO-qILr-XA0m4axi3oY8"
attributes=["interest", "time", "range"]
class User(ndb.Model): #traits is an array that's filled from the personal quiz
     email=ndb.StringProperty(required=True)
     traits=ndb.StringProperty(repeated=True)

class Restaurant(object):
    def __init__(self, n, p, r, b, t, a):#, la, ln):
        self.name=n
        self.plevel=int(p)
        self.rating=float(r)
        self.open=b
        self.types=t
        self.vicinity=a
        #self.lat=la
        #self.lon=ln

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
        about_template=jinja_env.get_template('templates/about.html')#load up the about page and access quotes api
        data=None
        url="https://api.forismatic.com/api/1.0/?method=getQuote&format=json&lang=en" #FORISMATIC API gets random quote
        bool=False
        quote=""
        author=""
        while bool==False:
            try:
                response=urlfetch.fetch(url)
                data=json.loads(response.content.replace(r'\x3E', '\x3E').replace('\r\n', '\\r\\n'))
                # returns {"quoteText":"Love is not blind; it simply enables one to see things others fail to see.", "quoteAuthor":"", "senderName":"", "senderLink":"", "quoteLink":"http://forismatic.com/en/848e15db47/"}
                quote=data["quoteText"]
                author=" - "+ data["quoteAuthor"]
                bool=True
            except ValueError:
                pass
        q={"quote":quote, "author":author}
        self.response.write(about_template.render(q))#add the form

class LoginPage(webapp2.RequestHandler):
    def get(self):
        user=users.get_current_user()
        if user:
            nickname=user.nickname()
            vars={"name":nickname}
            self.response.write("var")
            #self.redirect('/mood')
        else:
            self.redirect('/reciever')
        #login_template=jinja_env.get_template('templates/login.html')
        #self.response.write(login_template.render())#add the form

class LoginReciever(webapp2.RequestHandler): #if this is a user who didnt login
    def get(self):
        login_url=users.create_login_url("/mood")
        vars={"url":login_url}
        self.response.write('You are not logged in! Log in here: <a href="'+login_url+'">click here</a>')
        data=User.query().fetch() #does data return none if empty?
        if data==None: #if no one's made an account
            self.redirect('/account')
        else:
            self.redirect('/mood')

class AccountPage(webapp2.RequestHandler): #get, post
    def get(self):
        account_template=jinja_env.get_template('templates/account.html')
        self.response.write(account_template.render())

class DataRecieverPage(webapp2.RequestHandler): #get, post request in javascript
    def get(self):
        interest=self.request.get("interest")
        time=self.request.get("time")#outdoor, indoor
        range=self.request.get("range")
        email=""
        self.response.write(interest+" "+time+" "+range)
        user=users.get_current_user()
        vars={}
        if user:
            email=user.nickname()
        else:
            self.redirect('/reciever')
        traits={interest, time, str(range)}
        user=User(email=email, traits=traits)
        user.put()

class MoodPage(webapp2.RequestHandler): #get, post request in javascript
    def get(self):
        mood_template=jinja_env.get_template('templates/mood.html')
        user=users.get_current_user()
        if user:
            nickname=user.nickname()
            vars={"name":nickname}
            self.response.write(mood_template.render(vars))
        else:
            self.redirect('/reciever')
    #post method is done where in a javascript file, through button onclick, we can edit the html/css file there

class DailyRecPage(webapp2.RequestHandler): #get, post, keyError
    def get(self):
        #get user location through google maps api and detail the current time and location
        dailyrec_template=jinja_env.get_template('templates/dailyrec.html')
        date=ctime()
        url="https://www.googleapis.com/geolocation/v1/geolocate?key="+apikey
        self.response.write(url)
        self.response.write("<br>")
        response=urlfetch.fetch(url, method="POST")
        data=json.loads(response.content)
        lat=str(data["location"]["lat"])
        lon=str(data["location"]["lng"])
        self.response.write(lat+","+lon)
        #reverse geocode location to get the address
        url="https://maps.googleapis.com/maps/api/geocode/json?latlng="+lat+","+lon+"&key="+apikey
        response=urlfetch.fetch(url, method="POST")
        data=json.loads(response.content)
        address=data["results"][0]["formatted_address"]
        self.response.write(address)
        self.response.write(" -> displays activity recommendations based on personality quiz")
        vars={date,data,address}
        self.response.write(dailyrec_template.render(vars))

class FoodPage(webapp2.RequestHandler): #get, post
    def get(self):
        account_template=jinja_env.get_template('templates/food.html')
        #go to google places api
        #possibly put in jscript
        '''url="https://www.googleapis.com/geolocation/v1/geolocate?key="+apikey
        self.response.write(url)
        self.response.write(url)
        response=urlfetch.fetch(url, method="POST")
        data=json.loads(response.content)
        self.response.write("<br>")
        self.response.write(data)
        lat=str(data["location"]["lat"])
        lon=str(data["location"]["lng"])
        url="https://maps.googleapis.com/maps/api/place/nearbysearch/json?location="+lat+","+lon+"&radius=1500&type=restaurant&keyword=restaurant&key="+apikey
        self.response.write(url)
        self.response.write("<br>")
        response=urlfetch.fetch(url, method="POST")
        data=json.loads(response.content)
        dataset=data["results"]
        restaurants=[]
        for i in range(0, len(dataset)):
            value=dataset[i]
            u"{}".format(value)
            resta=None
            try:
                resta=Restaurant(value["name"], value["price_level"], value["rating"], value["opening_hours"]["open_now"], value["types"], value["vicinity"])
                restaurants.append(resta)
            except KeyError:
                pass
        for r in restaurants:
            #st=r.name+", Price: "+str(r.plevel)+", Rating: "+str(r.rating)+", IsOpen: "+str(r.open)+", Keywords: "+str(r.types)+", Approx. Address: "+r.vicinity#+", Lat: "+str(r.lat)+", Lon: "+str(r.lon)
            if r.open==True:
                self.response.write(data)
                self.response.write("<br>")
        url="https://maps.googleapis.com/maps/api/staticmap?center="+lat+","+lon+"&zoom=12&size=400x400&key="+apikey'''
        self.response.write(account_template.render())
#yoga api-indoor activity, video games api - indoor leisure
#landmark api-outdoor leisure, national parks- outdoor activity
class SocialPage(webapp2.RequestHandler): #get, post
    def get(self):
        #social_template=jinja_env.get_template('templates/social.html')
        url="https://maps.googleapis.com/maps/api/place/nearbysearch/json?location="+lat+","+lon+"&radius=1500&type=landmark&keyword=cruise&key="+apikey
        response=urlfetch.fetch(url, method="POST")
        data=json.loads(response.content)
        dataset=data["results"]
        self.response.write(dataset)
        #self.response.write(social_template.render())

class LeisurePage(webapp2.RequestHandler): #get, post
    def get(self):
        #exercise_template=jinja_env.get_template('templates/activity.html')
        #grab yoga api, google park, video games api
        #if you are an indoors person
        url="https://raw.githubusercontent.com/rebeccaestes/yoga_api/master/yoga_api.json"
        response=urlfetch.fetch(url)
        data=json.loads(response.content)
        index=random.randint(0, len(data)-1)
        name0=data[index]["english_name"]
        name=name0.replace(" ", "+")
        search=name+"+yoga+position"
        link="https://www.google.com/search?hl=en&biw=908&bih=868&tbm=isch&sa=1&ei=cLw5XfeEBPeT0PEPna-a6AY&q="+search+"&oq="+search+"&gs_l=img.3..35i39l2j0i67j0j0i67l4j0j0i67.15001.15354..15508...0.0..0.50.235.5......0....1..gws-wiz-img.bDzfPGJecS8&ved=0ahUKEwj3_NPco9DjAhX3CTQIHZ2XBm0Q4dUDCAY&uact=5"
        self.response.write(link)
        self.response.write("<br>")
        #img=data[index]["img_url"]
        self.response.write("<a href="+link+">"+name0+"</a>")#+img) #link text to link
        self.response.write("<br>")
        #self.response.write("<img src='"+img+"' width=200px height=200px />")
        vars={"name":name}#, "url":img}
        #self.response.write(exercise_template.render(vars))

#the app configuration
app=webapp2.WSGIApplication([ #about, login, create account, mood, daily recommendations, food, physical+leisure,
    ('/', AboutPage),
    ('/login', LoginPage),
    ('/account', AccountPage),
    ('/mood', MoodPage),
    ('/reciever', LoginReciever),
    ('/dailyrec', DailyRecPage),
    ('/food', FoodPage),
    ('/social', SocialPage),
    ('/activity', LeisurePage),
    ('/datareciever', DataRecieverPage),
], debug=True)  #array is all the routes in application (like home, about page)

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
#ADD BUTTON TO YOGA TO RANDOMIZE POSITIONS
apikey=""
giantbombkey=""
recs={}
class User(ndb.Model): #traits is an array that's filled from the personal quiz
     email=ndb.StringProperty(required=True)
     traits=ndb.StringProperty(repeated=True)
     attributes=ndb.StringProperty(repeated=True)
     color=ndb.StringProperty(required=True)

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
class Game(object):
    def __init__(self, n, l, i, s):
        self.name=n
        self.link=l
        self.imagelink=i
        self.stars=s

class Landmark(object):
    def __init__(self, n, r, b, t, a):#, la, ln):
        self.name=n
        self.rating=float(r)
        self.open=b
        self.types=t
        self.vicinity=a

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
        #print(user)
        if user:
            data=User.query().fetch()
            if len(data)==0: #if no one's made an account
                self.redirect('/account')
            else:
                self.redirect('/mood')
        else:
            login_url=users.create_login_url("/account")
            vars={"url":login_url}#{{url}}
            login_template=jinja_env.get_template('templates/login.html')
            self.response.write(login_template.render(vars))
            #self.response.write('You are not logged in! Log in here: <a href="'+login_url+'">click here</a>')

class LoginReciever(webapp2.RequestHandler): #if this is a user who didnt login
    def get(self):
        login_url=users.create_login_url("/mood")
        vars={"url":login_url}
        login_template=jinja_env.get_template('templates/login.html')
        data=User.query().fetch() #does data return none if empty?
        if data==None: #if no one's made an account
            self.redirect('/account')
        else:
            self.redirect('/mood')
        self.response.write(login_template.render(vars))

class LogoutPage(webapp2.RequestHandler):
    def get(self):
        logout_url=users.create_logout_url("/")
        #user=None
        #self.response.write("hello "+str(nickname))
        vars={"url":logout_url}
        logout_template=jinja_env.get_template('templates/logout.html')
        self.response.write(logout_template.render(vars))

class AccountPage(webapp2.RequestHandler): #get, post
    def get(self):
        user=users.get_current_user()
        #print(user)
        if user:
            account_template=jinja_env.get_template('templates/account.html')
            self.response.write(account_template.render())
        else:
            login_url=users.create_login_url("/account")
            vars={"url":login_url}
            login_template=jinja_env.get_template('templates/login.html')
            self.response.write(login_template.render(vars))

class DataRecieverPage(webapp2.RequestHandler): #get, post request in javascript
    def get(self):
        interest=str(self.request.get("interest"))
        time=str(self.request.get("time"))#outdoor, indoor
        range=str(self.request.get("points"))#plevel affected
        email=""
        exercise=str(self.request.get("exercise"))#often?->increases yoga timed exercises
        eater=str(self.request.get("eater")) #pickt? -> choose restaurants with increased ratings
        travel=str(self.request.get("travel")) #far? yes or no -> increase radius
        color="pink"
        #self.response.write(interest+" "+time+" "+range)
        user=users.get_current_user()
        vars={}
        if user:
            email=user.nickname()
            traits=[interest, time, range, exercise, eater, travel]
            #print(email+" "+str(traits))
            at=User.query().filter(User.email==email).fetch()
            if len(at)!=0:
                at[0].traits=traits
                at[0].attributes=["Are you an indoor or outdoor person?", "Do you prefer going out in the day or night?", "What is your preferred price range?", "How often do you exercise?", "Are you a picky eater?", "Do you enjoy traveling far?"]
                at[0].color=color
                at[0].put()
            else:
                attributes=["Are you an indoor or outdoor person?", "Do you prefer going out in the day or night?", "What is your preferred price range?", "How often do you exercise?", "Are you a picky eater?", "Do you enjoy traveling far?"]
                user=User(email=email, traits=traits, attributes=attributes, color=color)
                user.put()
        else:
            self.redirect('/reciever')
        self.redirect('/mood')

class MoodPage(webapp2.RequestHandler): #get, post request in javascript
    def get(self):
        mood_template=jinja_env.get_template('templates/mood.html')
        user=users.get_current_user() #CHANGE HAPPY LINK ON HTML TO logout
        if user:
            nickname=user.nickname()
            vars={"name":nickname}
            self.response.write(mood_template.render(vars))
        else:
            self.redirect('/reciever')

class DailyRecHandler(webapp2.RequestHandler): #get, post, keyError
    def get(self):
        #get user location through google maps api and detail the current time and location
        self.redirect('/dailyrec/pink')

class DailyRecPage(webapp2.RequestHandler): #get, post, keyError
    def get(self, data):
        dailyrec_template=jinja_env.get_template('templates/dailyrec.html')
        color=data
        vars={"color":color}
        user=users.get_current_user()
        attr=None
        if user:
            em=user.nickname()
            attr=User.query().filter(User.email==em).fetch()
            if len(attr)>0:
                attr[0].color=color
                attr[0].put()
            self.response.write(dailyrec_template.render(vars))
        else:
            self.redirect('/reciever')


class FoodHandler(webapp2.RequestHandler):#LINK http://localhost:8080/foodhandler on food tab
    def get(self):
        self.redirect('/food/22.4,-33.4')

class FoodPage(webapp2.RequestHandler): #get, post
    def get(self, data):
        food_template=jinja_env.get_template('templates/food.html')
        parsed=data.split(",")
        lat=float(parsed[0])
        lon=float(parsed[1])
        url="https://maps.googleapis.com/maps/api/place/nearbysearch/json?location="+str(lat)+","+str(lon)+"&radius=1500&type=restaurant&keyword=restaurant&key="
        response=urlfetch.fetch(url, method="POST")
        data=json.loads(response.content)
        dataset=data["results"]
        restaurants=[]
        for i in range(0, len(dataset)):
            value=dataset[i]
            resta=None
            try:
                print(str(value["vicinity"]))
                resta=Restaurant(str(value["name"]), str(value["price_level"]), str(value["rating"]), str(value["opening_hours"]["open_now"]), str(value["types"]), str(value["vicinity"]))
                restaurants.append(resta)
            except:
                pass
        #print(restaurants)
        count=0
        vars={}
        deliver=[]
        for r in restaurants:
            #st=r.name+", Price: "+str(r.plevel)+", Rating: "+str(r.rating)+", IsOpen: "+str(r.open)+", Keywords: "+str(r.types)+", Approx. Address: "+r.vicinity#+", Lat: "+str(r.lat)+", Lon: "+str(r.lon)
            if r.open=="True":
                count+=1
                deliver.append(r)
                #st=str(r.name)+", Price: "+str(r.plevel)+", Rating: "+str(r.rating)+", IsOpen: "+str(r.open)+", Keywords: "+str(r.types)+", Approx. Address: "+str(r.vicinity)
                #print(st)
                #self.response.write(st)#+", Lat: "+str(r.lat)+", Lon: "+str(r.lon))
                #self.response.write("<br>")
        vars["list"]=deliver
        if count==0:
            vars["startertext"]="All of the nearby found restaurants are not open at this time. Here is a general list:"
            for r in restaurants:
                deliver.append(r)
                '''st=str(r.name)+", Price: "+str(r.plevel)+", Rating: "+str(r.rating)+", IsOpen: "+str(r.open)+", Keywords: "+str(r.types)+", Approx. Address: "+str(r.vicinity)
                print(st)
                self.response.write(st)#+", Lat: "+str(r.lat)+", Lon: "+str(r.lon))
                self.response.write("<br>")'''
        else:
            vars["startertext"]="Here are the restaurants open at this time:"
        #print(restaurants[0].plevel)
        self.response.write(food_template.render(vars))
        #go to google places api
        #possibly put in jscript
class SocialHandler(webapp2.RequestHandler):#LINK http://localhost:8080/foodhandler on food tab
    def get(self):
        self.redirect('/social/22.4,-33.4')
#yoga api-indoor activity, video games api - indoor leisure
#landmark api-outdoor leisure, national parks- outdoor activity
class SocialPage(webapp2.RequestHandler): #get, post
    def get(self, data):
        social_template=jinja_env.get_template('templates/social.html')
        user=users.get_current_user()
        vars={}
        attr=None
        if user:
            em=user.nickname()
            attr=User.query().filter(User.email==em).fetch()
        else:
            self.redirect('/reciever')
        parsed=data.split(",")
        lat=float(parsed[0])
        lon=float(parsed[1])
        print(str(lat)+" "+str(lon))
        #url="https://maps.googleapis.com/maps/api/place/nearbysearch/json?location="+str(lat)+","+str(lon)+"&radius=1500&type=landmark&keyword=landmark&key="
        url="https://maps.googleapis.com/maps/api/place/search/json?key=&location="+str(lat)+","+str(lon)+"&radius=1500&sensor=false"
        #https://maps.googleapis.com/maps/api/place/search/json?key=&location=,&radius=1000&sensor=false
        response=urlfetch.fetch(url, method="POST")
        data=json.loads(response.content)
        dataset=data["results"]
        #print(data)
        #if nothing (len(dataset)==0) was found say that no nearby places availiable
        landmarks=[]
        for i in range(0, len(dataset)):
            value=dataset[i]
            #print(value)
            land=None
            try:
                land=Landmark(str(value["name"]), str(value["rating"]), str(value["opening_hours"]["open_now"]), str(value["types"]), str(value["vicinity"]))
                landmarks.append(land)
            except KeyError:
                pass
        count=0
        deliver=[]
        startertext=""
        for r in landmarks:
            #st=r.name+", Price: "+str(r.plevel)+", Rating: "+str(r.rating)+", IsOpen: "+str(r.open)+", Keywords: "+str(r.types)+", Approx. Address: "+r.vicinity#+", Lat: "+str(r.lat)+", Lon: "+str(r.lon)
            if r.open=="True":
                startertext="Here are the landmarks open at this time:"
                count+=1
                deliver.append(r)
                '''st=r.name+", Rating: "+str(r.rating)+", IsOpen: "+str(r.open)+", Keywords: "+str(r.types)+", Approx. Address: "+r.vicinity
                #print(st)
                self.response.write(st)#+", Lat: "+str(r.lat)+", Lon: "+str(r.lon))
                self.response.write("<br>")'''

            if count==0:
                startertext="All of the nearby found places are not open at this time. Below is a general list:"
                for r in landmarks:
                    deliver.append(r)
                    '''st=str(r.name)+", Price: "+str(r.plevel)+", Rating: "+str(r.rating)+", IsOpen: "+str(r.open)+", Keywords: "+str(r.types)+", Approx. Address: "+str(r.vicinity)
                    print(st)
                    self.response.write(st)#+", Lat: "+str(r.lat)+", Lon: "+str(r.lon))
                    self.response.write("<br>")'''
        vars={
        "list":deliver,
        "startertext":startertext
        }
        self.response.write(social_template.render(vars))

class LeisurePage(webapp2.RequestHandler): #get, post
    def get(self):
        #exercise_template=jinja_env.get_template('templates/activity.html')
        #grab yoga api, google park, video games api
        #if you are an indoors person
        '''
https://www.google.com/search?source=hp&ei=JEY-XcDBOeis0gLz56RA&q="+place.name.replace(' ', '+')+'+'+place.location.replace(' ', '+')+"&oq="+place.name.replace(' ', '+')+'+'+place.location.replace(' ', '+')+&gs_l=psy-ab.3..0l10.1326.1565..1744...1.0..0.237.375.3j0j1....3..0....1..gws-wiz.....10..35i39.6OXg5ZQE-dc&ved=0ahUKEwjA48TO99jjAhVollQKHfMzCQgQ4dUDCAc&uact=5

        '''
        activity_template=jinja_env.get_template('templates/yoga.html')
        url="https://raw.githubusercontent.com/rebeccaestes/yoga_api/master/yoga_api.json"
        response=urlfetch.fetch(url)
        data=json.loads(response.content)
        index=random.randint(0, len(data)-1)
        name0=data[index]["english_name"]
        name=name0.replace(" ", "+")
        search=name+"+yoga+position"
        link="https://www.google.com/search?hl=en&biw=908&bih=868&tbm=isch&sa=1&ei=cLw5XfeEBPeT0PEPna-a6AY&q="+search+"&oq="+search+"&gs_l=img.3..35i39l2j0i67j0j0i67l4j0j0i67.15001.15354..15508...0.0..0.50.235.5......0....1..gws-wiz-img.bDzfPGJecS8&ved=0ahUKEwj3_NPco9DjAhX3CTQIHZ2XBm0Q4dUDCAY&uact=5"
        #self.response.write(link)
        #self.response.write("<br>")
        img=data[index]["img_url"]
        #self.response.write("<a href="+link+">"+name0+"</a>")#+img) #link text to link
        #self.response.write("<br>")
        #self.response.write("<img src='"+img+"' width=200px height=200px />")
        vars={"link":link, "name":name0}#, "url":img}
        self.response.write(activity_template.render(vars))

class FoodRecHandler(webapp2.RequestHandler):#LINK http://localhost:8080/foodhandler on food tab
    def get(self):
        self.redirect('/foodrec/22.4,-33.4')

class FoodRecPage(webapp2.RequestHandler): #display best choices based on places
    def get(self, data):
        user=users.get_current_user()
        vars={}
        attr=None
        foodrec_template=jinja_env.get_template('templates/foodrec.html')
        if user:
            em=user.nickname()
            attr=User.query().filter(User.email==em).fetch()
            if len(attr)==0:
                self.redirect('/account')
            else:
                choices=[]
                recs=[]
                for v in attr[0].traits:
                    choices.append(str(v))
                parsed=data.split(",")
                lat=float(parsed[0])
                lon=float(parsed[1])
                radius="1500"
                if choices[len(choices)-1]=="yes":
                    radius="3000"
                url="https://maps.googleapis.com/maps/api/place/nearbysearch/json?location="+str(lat)+","+str(lon)+"&radius="+radius+"&type=restaurant&keyword=restaurant&key="
                response=urlfetch.fetch(url, method="POST")
                data=json.loads(response.content)
                dataset=data["results"]
                restaurants=[]
                for i in range(0, len(dataset)):
                    value=dataset[i]
                    resta=None
                    try:
                        if str(value["opening_hours"]["open_now"])=="True":
                            resta=Restaurant(str(value["name"]), str(value["price_level"]), str(value["rating"]), str(value["opening_hours"]["open_now"]), str(value["types"]), str(value["vicinity"]))
                            restaurants.append(resta)
                            #st=resta.name+", Rating: "+str(resta.rating)+", IsOpen: "+str(resta.open)+", Keywords: "+str(resta.types)+", Approx. Address: "+resta.vicinity
                            #print(st)
                            #self.response.write(st)#+", Lat: "+str(r.lat)+", Lon: "+str(r.lon))
                            #self.response.write("<br>")
                    except:
                        pass
                extrachoices=[]
                #choices: ['indoor', 'day', '3', 'daily', 'yes', 'yes']
                chosenplevel=str(choices[2])
                plevellist=filter(lambda r: int(r.plevel)==int(chosenplevel), restaurants)
                ratinglist=sorted(plevellist, key=lambda x:-x.rating)
                bestchoices=[value for value in ratinglist if value in plevellist]
                print(bestchoices)
                startertext=""
                deliver=[]
                if len(bestchoices)>0:
                    startertext="Top choices"
                    vars={
                    "startertext":startertext,
                    "list":bestchoices,
                    "time":str(ctime())
                    }
                    self.response.write(foodrec_template.render(vars))
                else:
                    if len(ratinglist)>0:
                        startertext="Locations wih higher ratings"
                        vars={
                        "startertext":startertext,
                        "list":ratinglist,
                        "time":str(ctime())
                        }
                        self.response.write(foodrec_template.render(vars))
                        '''self.response.write("Top choices")
                        self.response.write("<br>")
                        for v in ratinglist:
                            st=v.name+", Rating: "+str(v.rating)+", IsOpen: "+str(v.open)+", Keywords: "+str(v.types)+", Approx. Address: "+v.vicinity+" Plevel: "+str(v.plevel)
                            self.response.write(st)
                            self.response.write("<br>")'''
                    if len(plevellist)>0:
                        startertext="Locations with same pricing level"
                        vars={
                        "startertext":startertext,
                        "list":plevelist,
                        "time":str(ctime())
                        }
                        self.response.write(foodrec_template.render(vars))
                    if len(plevellist)==0 and len(ratinglist)==0:
                        startertext="No optimal locations found at this time"
                        vars={
                        "startertext":startertext,
                        "list":[],
                        "time":str(ctime())
                        }
                        self.response.write(foodrec_template.render(vars))
        else:
            self.redirect('/reciever')
        #attributes=["interest", "time", "range", "exercise", "eater", "travel"]'''

class YogaRecPage(webapp2.RequestHandler):
    def get(self):
        '''
        https://api.rawg.io/api/games/grand-theft-auto-v?source=post_page
        ["name"]
        ["parent_platforms"] is list -> iterate ["platform"]["name"]
        ["ratings"] is list -> ["title"] and ["count"]
        ["released"] is list -> ["background_image"]
        pickiness taken into account -^
        '''
        user=users.get_current_user()
        #if indoor recommend general places
        #if outdoor recommend parks
        if user:
            em=user.nickname()
            attr=User.query().filter(User.email==em).fetch()
            if len(attr)==0:
                self.redirect('/account')
            else:
                choices=[]
                for v in attr[0].traits:
                    choices.append(str(v))
                deliver=[]
                if choices[3]=='no': #daily monthly, weekly no
                    #self.response.write("Want to be relaxed today?")
                    game_template=jinja_env.get_template('templates/gamerec.html')
                    url="http://www.giantbomb.com/api/games/?api_key="+giantbombkey+"&sort=original_release_date:des&format=json"
                    response=urlfetch.fetch(url)
                    data=json.loads(response.content)
                    datafinding=None
                    fitdata=[]
                    for ind in range(0, 50):
                        if len(fitdata)!=1:
                            gamename=data["results"][ind]["name"]
                            #print(imglink)
                            #print(gamename)
                            findlink="https://api.rawg.io/api/games/"+gamename.replace(' ', '-')+"?source=post_page"
                            #print(findlink)
                            try:
                                response=urlfetch.fetch(findlink)
                                datafinding=json.loads(response.content)
                                try:
                                    if datafinding["esrb_rating"]!=None:
                                        if datafinding!=None and datafinding!={"detail":"Not found."} and datafinding["esrb_rating"]["name"].lower()!="mature":
                                            '''self.name=n
                                            self.link=l
                                            self.imagelink=i
                                            self.stars=s'''
                                            tgname=datafinding["name"]
                                            tgwebsite=datafinding["website"]
                                            tgimagelink=datafinding["background_image"]
                                            #print(tgimagelink)
                                            tgstars=datafinding["rating"]
                                            agame=Game(tgname, tgwebsite, tgimagelink, tgstars)
                                            fitdata.append(agame)
                                            #print(agame)
                                except KeyError:
                                    continue
                            except ValueError:
                                continue
                        else:
                            break
                    #print(deliver)
                    #print(fitdata)
                    for i in fitdata:
                        deliver.append(i)
                    vars={"games":deliver}
                    self.response.write(game_template.render(vars))
                else:
                    p_template=jinja_env.get_template('templates/yoga.html')
                    url="https://raw.githubusercontent.com/rebeccaestes/yoga_api/master/yoga_api.json"
                    response=urlfetch.fetch(url)
                    data=json.loads(response.content)
                    index=random.randint(0, len(data)-1)
                    if data[index]["english_name"].lower()=="cow":
                        index=random.randint(0, len(data)-1)
                    name0=data[index]["english_name"]
                    name=name0.replace(" ", "+")
                    search=name+"+yoga+position"
                    link="https://www.google.com/search?hl=en&biw=908&bih=868&tbm=isch&sa=1&ei=cLw5XfeEBPeT0PEPna-a6AY&q="+search+"&oq="+search+"&gs_l=img.3..35i39l2j0i67j0j0i67l4j0j0i67.15001.15354..15508...0.0..0.50.235.5......0....1..gws-wiz-img.bDzfPGJecS8&ved=0ahUKEwj3_NPco9DjAhX3CTQIHZ2XBm0Q4dUDCAY&uact=5"
                    img=data[index]["img_url"]
                    vars={"link":link, "name":name0}#, "url":img}
                    self.response.write(p_template.render(vars))
        else:
            login_url=users.create_login_url("/account")
            vars={"url":login_url}
            login_template=jinja_env.get_template('templates/login.html')
            self.response.write(login_template.render(vars))

class PlaceRecHandler(webapp2.RequestHandler):#LINK http://localhost:8080/foodhandler on food tab
    def get(self):
        self.redirect('/placerec/22.4,-33.4')

class PlaceRecPage(webapp2.RequestHandler):
    def get(self, data):
        user=users.get_current_user()
        vars={}
        attr=None
        placerec_template=jinja_env.get_template('templates/placerec.html')
        #if indoor recommend general places
        #if outdoor recommend parks
        if user:
            em=user.nickname()
            attr=User.query().filter(User.email==em).fetch()
            if len(attr)==0:
                self.redirect('/account')
            else:
                choices=[]
                recs=[]
                for v in attr[0].traits:
                    choices.append(str(v))
                parsed=data.split(",")
                lat=float(parsed[0])
                lon=float(parsed[1])
                radius="1500"
                if choices[len(choices)-1]=="yes":
                    radius="3000"
                url=""
                if choices[0]=='indoor':
                    url="https://maps.googleapis.com/maps/api/place/search/json?key=&location="+str(lat)+","+str(lon)+"&radius="+radius+"&sensor=false"
                    response=urlfetch.fetch(url, method="POST")
                    data=json.loads(response.content)
                    dataset=data["results"]
                    landmarks=[]
                    for i in range(0, len(dataset)):
                        value=dataset[i]
                        land=None
                        try:
                            if str(value["opening_hours"]["open_now"])=="True":
                                land=Landmark(str(value["name"]), str(value["rating"]), str(value["opening_hours"]["open_now"]), str(value["types"]), str(value["vicinity"]))
                                landmarks.append(land)
                                #st=resta.name+", Rating: "+str(resta.rating)+", IsOpen: "+str(resta.open)+", Keywords: "+str(resta.types)+", Approx. Address: "+resta.vicinity
                                #print(st)
                                #self.response.write(st)#+", Lat: "+str(r.lat)+", Lon: "+str(r.lon))
                                #self.response.write("<br>")
                        except KeyError:
                            pass
                    #extrachoices=[]
                    #choices: ['indoor', 'day', '3', 'daily', 'yes', 'yes']
                    #chosenplevel=str(choices[len(choices)])
                    #plevellist=filter(lambda r: int(r.plevel)==int(chosenplevel), restaurants)
                    ratinglist=sorted(landmarks, key=lambda x:-x.rating)
                    startertext=""
                    deliver=[]
                    if len(ratinglist)>0:
                        startertext="Top choices:"
                        for v in ratinglist:
                            if v.open=="True":
                                deliver.append(v)
                                '''st=v.name+", Rating: "+str(v.rating)+", IsOpen: "+str(v.open)+", Keywords: "+str(v.types)+", Approx. Address: "+v.vicinity
                                self.response.write(st)
                                self.response.write("<br>")'''
                    else:
                        startertext="Locations not found that are open at this time. Below is general list:"
                        #self.response.write("<br>")
                        for v in ratinglist:
                            deliver.append(v)
                            '''st=v.name+", Rating: "+str(v.rating)+", IsOpen: "+str(v.open)+", Keywords: "+str(v.types)+", Approx. Address: "+v.vicinity
                            self.response.write(st)
                            self.response.write("<br>")'''
                    vars={
                        "list":deliver,
                        "startertext":startertext
                        }
                    self.response.write(placerec_template.render(vars))
                if choices[0]=='outdoor':
                    url="https://maps.googleapis.com/maps/api/place/nearbysearch/json?location="+str(lat)+","+str(lon)+"&radius="+radius+"&type=park&keyword=park&key="
                    response=urlfetch.fetch(url, method="POST")
                    data=json.loads(response.content)
                    dataset=data["results"]
                    landmarks=[]
                    for i in range(0, len(dataset)):
                        value=dataset[i]
                        land=None
                        try:
                            if str(value["opening_hours"]["open_now"])=="True":
                                land=Landmark(str(value["name"]), str(value["rating"]), str(value["opening_hours"]["open_now"]), str(value["types"]), str(value["vicinity"]))
                                landmarks.append(land)
                                #st=resta.name+", Rating: "+str(resta.rating)+", IsOpen: "+str(resta.open)+", Keywords: "+str(resta.types)+", Approx. Address: "+resta.vicinity
                                #print(st)
                                #self.response.write(st)#+", Lat: "+str(r.lat)+", Lon: "+str(r.lon))
                                #self.response.write("<br>")
                        except KeyError:
                            pass
                    #extrachoices=[]
                    #choices: ['indoor', 'day', '3', 'daily', 'yes', 'yes']
                    #chosenplevel=str(choices[len(choices)])
                    #plevellist=filter(lambda r: int(r.plevel)==int(chosenplevel), restaurants)
                    ratinglist=sorted(landmarks, key=lambda x:-x.rating)
                    startertext=""
                    deliver=[]
                    if len(ratinglist)>0:
                        startertext="Top choices:"
                        for v in ratinglist:
                            if v.open=="True":
                                deliver.append(v)
                                '''st=v.name+", Rating: "+str(v.rating)+", IsOpen: "+str(v.open)+", Keywords: "+str(v.types)+", Approx. Address: "+v.vicinity
                                self.response.write(st)
                                self.response.write("<br>")'''
                    else:
                        startertext="Locations not found that are open at this time. Below is general list:"
                        for v in ratinglist:
                            deliver.append(v)
                            '''st=v.name+", Rating: "+str(v.rating)+", IsOpen: "+str(v.open)+", Keywords: "+str(v.types)+", Approx. Address: "+v.vicinity
                            self.response.write(st)
                            self.response.write("<br>")'''
                    vars={
                    "list":deliver,
                    "startertext":startertext,
                    "time":str(ctime())
                    }
                    self.response.write(placerec_template.render(vars))
        else:
            self.redirect('/reciever')
        #attributes=["interest", "time", "range", "exercise", "eater", "travel"]'''
'''
                attributes=["Are you an indoor or outdoor person?", "Do you prefer going out in the day or night?", "What is your preferred price range?", "Would you like to exercise today?", "Are you a picky eater?", "Do you enjoy traveling far?"]
                choosing restaurants:
                    choose in price range, picky eater get top rated, farness doubles radius used to affect the scope

                        eater and exercise and travel:yes, no; interest: indoor, outdoor;
                        time: day, night; range: 1-4
                        self.name=n
                        self.plevel=int(p)
                        self.rating=float(r)
                        self.open=b
                        self.types=t
                        self.vicinity=a
'''
#the app configuration
app=webapp2.WSGIApplication([ #about, login, create account, mood, daily, recommendations, food, physical+leisure,
    ('/', AboutPage),
    ('/login', LoginPage),
    ('/account', AccountPage),
    ('/mood', MoodPage),
    ('/reciever', LoginReciever),
    ('/dailyrec/(.*)', DailyRecPage),
    ('/dailyrechandler', DailyRecHandler),
    ('/food/(.*)', FoodPage),
    ('/foodhandler', FoodHandler),
    ('/logout', LogoutPage),
    ('/social/(.*)', SocialPage),
    ('/socialhandler', SocialHandler),
    ('/activity', LeisurePage),
    ('/datareciever', DataRecieverPage),
    ('/foodrec/(.*)', FoodRecPage),
    ('/foodrechandler', FoodRecHandler),
    ('/yogarec', YogaRecPage),
    ('/placerec/(.*)', PlaceRecPage),
    ('/placerechandler', PlaceRecHandler),
    ('/about', AboutPage),
], debug=True)  #array is all the routes in application (like home, about page)

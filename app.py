from flask import Flask, Response, request, jsonify, render_template, session, redirect, url_for
from database import DatabaseConnection
import datetime, bcrypt
import os
import pandas as pd
import tweepy as tw
from google.cloud import language
from google.cloud.language import enums
from google.cloud.language import types
from google.cloud import language_v1
import datetime as DT
import random
from opencage.geocoder import OpenCageGeocode
from pprint import pprint
import requests
import json

app = Flask(__name__)
db = DatabaseConnection()

consumer_key = 'P9NVb0v1F0mLVQA8zwbq7bGwy'
consumer_secret = '6H6KVEZB6WZjvweQEML7cwxg1oc615Chb0nRolJJVDKkL5B4Zr'
access_token = '2622392858-deLZuS9SRolzoAQP2K9WYJN2T7Brv1O8tOBfXBY'
access_token_secret = 'ViyktIVvgOKlpW3yKLRVD4Ot2cSEvXQ3VOeSpeS2KWVeo'
opencage_key = '44afc67e2f724510abc4bd3706dd070b'
darksky_key = '18361e6c321dc572643adebd1bfe93d5'

auth = tw.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
api = tw.API(auth, wait_on_rate_limit=True)
geocoder = OpenCageGeocode(opencage_key)

client = language.LanguageServiceClient()
type_ = enums.Document.Type.PLAIN_TEXT
language = "en"
encoding_type = enums.EncodingType.UTF8

# @app.route("/result", methods=["GET"])
# def result():
#     return render_template("result.html")

@app.route("/analyze", methods=["POST", "GET"])
def analyze():
    if (request.method == 'POST'):
        document = {
            "answer1" : request.form['answer1'],
            "answer2" : request.form['answer2'],
            "answer3" : request.form['answer3'],
            "answer4" : request.form['answer4'],
            "answer5" : request.form['answer5'],
        }
        current_user = db.findOne('users', {"username": session["username"]})
        location = current_user["city"]+','+current_user["state"]
        ans = [document['answer1'], document['answer2'],document['answer3'], document['answer4'], document['answer5']]
        savingGoal = getSavingGoal(int(current_user['income']),ans, location)
        db.update('users', {'username': session['username']}, {'$set': {'savingGoal': savingGoal}})
        if annotateAnswers(ans) < 0 :
            message = "Sometimes spending just a little more can be rewarding. We feel like this is one of those times, so we have customized a list of things you can buy in exchange for happiness."
            choice = ['Discount on car maintainance','Discount on future house maintainance', 'Discount on wedding services']
        else:
            message = "We value your happiness and are willing to go to great lengths to ensure it. With our saving options, you can rest assured knowing you have commited to a long term investment in future happiness."
            choice = ['Voucher for spa', 'Discount for Whole Food','Charity or gifting a friend']
        return render_template("result.html", savingGoal=savingGoal, message=message, choice1=choice[0], choice2=choice[1], choice3=choice[2])

    return render_template("analyze.html")


@app.route("/result", methods=["POST", "GET"])
def result():
    current_user = db.findOne('users', {"username": session["username"]})
    return render_template("index.html", alert="You have chosen "+ request.form['choice']+'!', income=current_user['income'], savingGoal=current_user['savingGoal'])



@app.route("/financials", methods=["POST", "GET"])
def financials():
    if (request.method == 'POST'):
        db.update('users', {'username': session['username']},{ '$set' :{'income' : request.form['income']}})
        current_user = db.findOne('users', {"username": session["username"]})
        return render_template("index.html", alert="Net income updated!", income=current_user['income'], savingGoal=current_user['savingGoal'])

    return render_template("financials.html")

@app.route("/", methods=["GET"])
# home page 
def index(): 
    if session.get('logged_in') != None:
        if session.get('logged_in') == False:
            return redirect(url_for('login')) 
        current_user = db.findOne('users', {"username": session["username"]})
        return render_template("index.html",income = current_user['income'], savingGoal = current_user['savingGoal'])
    else: 
        return redirect(url_for('login'))

@app.route("/login", methods=["POST", "GET"])
def login():
    if session.get('logged_in') == True:
        return redirect(url_for('index'))
    error = None
    if request.method == "POST":
        login_user = db.findOne("users", {"username": request.form["username"]})
        if login_user:
            # check if password is correct
            if bcrypt.hashpw(request.form['pass'].encode('utf-8'), login_user['password']) == login_user['password']:
                session['username'] = request.form['username']
                session['first_name'] = login_user["first_name"]
                session['logged_in'] = True
                return redirect(url_for('index'))
            error = "Invalid username or password"
        else:
            error = "Invalid username or password"

    return render_template("login.html", error=error)

@app.route("/register", methods=["POST", "GET"])
def register():
    if session.get('logged_in') == True:
        return redirect(url_for('index'))
    error = None
    if request.method == "POST":
        existing_user = db.findOne("users", {"username": request.form["username"]})
        # if username is not in db, create new user
        if existing_user is None:
            hashpass = bcrypt.hashpw(request.form["pass"].encode("utf-8"), bcrypt.gensalt())
            document = {
                "username": request.form["username"],
                "password": hashpass,
                "first_name": request.form["first"],
                "last_name": request.form["last"],
                "city": request.form["city"],
                "state": request.form["state"],
                "income": 0,
                "savingGoal": 0
            }
            db.insert("users", document)
            session["username"] = request.form["username"]
            session['first_name'] = request.form["first"]
            session['logged_in'] = True
            return redirect(url_for("index"))
        error = "The username already exists" 
        #else:
            #error = "Invalid username"  
    
    return render_template("register.html", error=error)

@app.route("/logout")
def logout():
    session.pop('logged_in', None)
    return redirect(url_for("login"))


#get the sentiment score and magnitude of a text, return the product of score and magnitude
def annotateAnswers(ans_array):
    ret = 0
    for ans in ans_array:
        document = {"content": ans, "type": type_, "language": language}
        annotations = client.analyze_sentiment(document=document)
        score = annotations.document_sentiment.score
        magnitude = annotations.document_sentiment.magnitude
        ret += score * magnitude
    return ret / len(ans_array)

#get the sentiment score and magnitude of a tweet within the past week that contains a random word in text, return the product of score and magnitude
def getRandomTwitter(ans_array):
    ret = 0
    for ans in ans_array:
        arr_of_text = ans.split()
        word = random.choice(arr_of_text)
        new_search = word + " -filter:retweets"
        today = DT.date.today()
        week_ago = today - DT.timedelta(weeks=4)
        tweets = tw.Cursor(api.search,
                            q=new_search,
                            lang="en",
                            since=week_ago).items(50)
        random_tweet = random.choice([tweet.text for tweet in tweets])
        document = {"content": random_tweet,
                    "type": type_, "language": language}
        annotations = client.analyze_sentiment(document=document)
        score = annotations.document_sentiment.score
        magnitude = annotations.document_sentiment.magnitude
        ret += score * magnitude
    return ret / len(ans_array)


def getWeatherVariable(city_name):
    result = geocoder.geocode(city_name, no_annotations='1')
    lat = result[0]['geometry']['lat']
    lng = result[0]['geometry']['lng']
    forecast = requests.get('https://api.darksky.net/forecast/' + darksky_key+'/'+str(
        lat)+','+str(lng)+"?&exclude=currently,minutely,hourly,alerts,flags&units=si").json()
    mood = 0
    for i in range(8):
        mood += getWeatherMoodVariable(forecast['daily']['data'][i]['precipProbability'], forecast['daily']['data'][i]['cloudCover'])
    return mood/8


#an algorithm that return a number between 0 and 1, where 1 is positive and 0 is negative
def getWeatherMoodVariable(precipProb, cloud):
    return (1 - precipProb * cloud)


#return saving percentage
def getSavingPercentage(arr):
    text_variable = arr[0]
    twitter_variable = arr[1]
    weather_variable = arr[2]

    return 10 * (0.7 * text_variable + 0.2 * weather_variable + 0.1 * twitter_variable) + 6


def getSavingGoal(inc, arr_of_ans, location):
    ret = inc * (getSavingPercentage([annotateAnswers(arr_of_ans), getRandomTwitter(arr_of_ans), getWeatherVariable(location)])/100)
    return round(ret, 2)




if __name__ == "__main__":
    app.secret_key = "secretkey"
    app.run(host="localhost", port=4000, debug=True)

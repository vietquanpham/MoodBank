from flask import Flask, Response, request, jsonify, render_template, session, redirect, url_for
from database import DatabaseConnection
import datetime, bcrypt
import os
import pandas as pd
import tweepy as tw
import datetime as DT
import random
from opencage.geocoder import OpenCageGeocode
from pprint import pprint
import requests
import json
import config
from joblib import load

app = Flask(__name__)
# db = DatabaseConnection()

consumer_key = config.consumer_key
consumer_secret = config.consumer_secret
access_token = config.access_token
access_token_secret = config.access_token_secret
opencage_key = config.opencage_key
darksky_key = config.darksky_key

auth = tw.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
api = tw.API(auth, wait_on_rate_limit=True)
geocoder = OpenCageGeocode(opencage_key)


bigram_vectorizer = load('data_preprocessors/bigram_vectorizer.joblib')
bigram_tf_idf_transformer = load('data_preprocessors/bigram_tf_idf_transformer.joblib')
sgd_classifier = load('classifiers/sgd_classifier.joblib')

@app.route("/analyze", methods=["POST", "GET"])
def analyze():
    if (request.method == 'POST'):
        document = {
            "income": request.form['income'],
            "answer1" : request.form['answer1'],
            "answer2" : request.form['answer2'],
            "answer3" : request.form['answer3'],
            "answer4" : request.form['answer4'],
            "answer5" : request.form['answer5'],
        }
        # current_user = db.findOne('users', {"username": session["username"]})
        location = "Boston, Massachusetts"
        income = int(document['income'])
        ans = [document['answer1'], document['answer2'],document['answer3'], document['answer4'], document['answer5']]
        savingGoal = getSavingGoal(income,ans, location)
        # db.update('users', {'username': session['username']}, {'$set': {'savingGoal': savingGoal}})
        if annotateAnswers(ans) < 0.5 :
            message = "Sometimes spending just a little more can be rewarding. We feel like this is one of those times, so we have customized a list of things you can buy in exchange for happiness."
            choice = ['Voucher for spa', 'Discount for Whole Food','Charity or gifting a friend']
        else:
            message = "We value your happiness and are willing to go to great lengths to ensure it. With our saving options, you can rest assured knowing you have commited to a long term investment in future happiness."
            choice = ['Discount on car maintainance','Discount on future house maintainance', 'Discount on wedding services']
        return render_template("result.html", savingGoal=savingGoal, message=message, choice1=choice[0], choice2=choice[1], choice3=choice[2])

    return render_template("analyze.html")


@app.route("/result", methods=["POST", "GET"])
def result():
    # current_user = db.findOne('users', {"username": session["username"]})
    # return render_template("index.html", alert="You have chosen "+ request.form['choice']+'!', income=current_user['income'], savingGoal=current_user['savingGoal'])
    return render_template("analyze.html")


# @app.route("/financials", methods=["POST", "GET"])
# def financials():
#     if (request.method == 'POST'):
#         db.update('users', {'username': session['username']},{ '$set' :{'income' : request.form['income']}})
#         current_user = db.findOne('users', {"username": session["username"]})
#         return render_template("index.html", alert="Net income updated!", income=current_user['income'], savingGoal=current_user['savingGoal'])

#     return render_template("financials.html")

# @app.route("/", methods=["GET"])
# # home page 
# def index(): 
#     if session.get('logged_in') != None:
#         if session.get('logged_in') == False:
#             return redirect(url_for('login')) 
#         current_user = db.findOne('users', {"username": session["username"]})
#         return render_template("index.html",income = current_user['income'], savingGoal = current_user['savingGoal'])
#     else: 
#         return redirect(url_for('login'))

# @app.route("/login", methods=["POST", "GET"])
# def login():
#     if session.get('logged_in') == True:
#         return redirect(url_for('index'))
#     error = None
#     if request.method == "POST":
#         login_user = db.findOne("users", {"username": request.form["username"]})
#         if login_user:
#             # check if password is correct
#             if bcrypt.hashpw(request.form['pass'].encode('utf-8'), login_user['password']) == login_user['password']:
#                 session['username'] = request.form['username']
#                 session['first_name'] = login_user["first_name"]
#                 session['logged_in'] = True
#                 return redirect(url_for('index'))
#             error = "Invalid username or password"
#         else:
#             error = "Invalid username or password"

#     return render_template("login.html", error=error)

# @app.route("/register", methods=["POST", "GET"])
# def register():
#     if session.get('logged_in') == True:
#         return redirect(url_for('index'))
#     error = None
#     if request.method == "POST":
#         existing_user = db.findOne("users", {"username": request.form["username"]})
#         # if username is not in db, create new user
#         if existing_user is None:
#             hashpass = bcrypt.hashpw(request.form["pass"].encode("utf-8"), bcrypt.gensalt())
#             document = {
#                 "username": request.form["username"],
#                 "password": hashpass,
#                 "first_name": request.form["first"],
#                 "last_name": request.form["last"],
#                 "city": request.form["city"],
#                 "state": request.form["state"],
#                 "income": 0,
#                 "savingGoal": 0
#             }
#             db.insert("users", document)
#             session["username"] = request.form["username"]
#             session['first_name'] = request.form["first"]
#             session['logged_in'] = True
#             return redirect(url_for("index"))
#         error = "The username already exists" 
#         #else:
#             #error = "Invalid username"  
    
#     return render_template("register.html", error=error)

# @app.route("/logout")
# def logout():
#     session.pop('logged_in', None)
#     return redirect(url_for("login"))


#get the sentiment score and magnitude of a text
def annotateAnswers(ans_array):
    ans_sentiment = []
    for ans in ans_array:
        ans_bigram = bigram_vectorizer.transform([ans])
        ans_bigram_tf_idf = bigram_tf_idf_transformer.transform(ans_bigram)
        ans_sentiment.append(sgd_classifier.predict(ans_bigram_tf_idf)[0])
    
    # covert the answer score from 0 to 5 to somewhere between 0 and 1, 1 means positive mood, 0 means negative mood.
    return sum(ans_sentiment) / 5


#get the sentiment score and magnitude of a tweet within the past week that contains a random word in each of the answer
def getRandomTwitter(ans_array):
    twit_sentiment = []
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
        twit_bigram = bigram_vectorizer.transform([random_tweet])
        twit_bigram_tf_idf = bigram_tf_idf_transformer.transform(twit_bigram)
        twit_sentiment.append(sgd_classifier.predict(twit_bigram_tf_idf)[0])
    return sum(twit_sentiment) / 5


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


#return a number between 0 and 1, where 1 is positive and 0 is negative. The idea is that higher precipitation probability and higher cloud density means lower mood
#and vice versa
def getWeatherMoodVariable(precipProb, cloud):
    return (1 - precipProb * cloud)


#return saving percentage
def getSavingPercentage(arr):
    text_variable = arr[0]
    twitter_variable = arr[1]
    weather_variable = arr[2]

    return 10 * (0.7 * text_variable + 0.2 * weather_variable + 0.1 * twitter_variable) + 10 # give each variable a weight, returns a percentage between 10 and 20. 


def getSavingGoal(inc, arr_of_ans, location):
    ret = inc * (getSavingPercentage([annotateAnswers(arr_of_ans), getRandomTwitter(arr_of_ans), getWeatherVariable(location)])/100)
    return round(ret, 2)




if __name__ == "__main__":
    app.secret_key = "secretkey"
    app.run(host="localhost", port=4000, debug=True)

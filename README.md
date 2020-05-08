# MoodBank

This is a modified version of the app that is used for CAS LX496 Project. The sentiment's analyser have been replaced by a model that was trained
using sklearn. The idea is simple: analyze the user's mood based on their answers on serveral question, combining with the weather data and some 
randomness from Twitter, the app will return a certain amount of money the user should save in this month based on their income. 

The learning model was trained using 1000 IMDB movie reviews. A major disadvantage of this model compare to using the Google NLP's service is that 
it only return discrete results of 1 or 0 for each answers, which is limited compare to Google's, in which it would return a score and a magnitude.

Serveral features have been remove to simplify the project. To run this project, first open terminal and type "pip install -r requirements.txt" to get all the dependencies, then run the file "application.py", and head to http://localhost:4000/ to use the app. It may take a while for the analyser to run.


Reference for this project: https://towardsdatascience.com/building-a-sentiment-classifier-using-scikit-learn-54c8e7c5d2f0
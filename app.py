from flask import Flask, Response, request, jsonify, render_template, session, redirect, url_for
from database import DatabaseConnection
import datetime, bcrypt

app = Flask(__name__)
db = DatabaseConnection()


@app.route("/", methods=["GET"])
# home page 
def index(): 
    if session.get('logged_in') == False:
        return redirect(url_for("login")) 
    return render_template("index.html")

@app.route("/login", methods=["POST", "GET"])
def login():
    error = None
    if request.method == "POST":
        login_user = db.findOne("users", {"username": request.form["username"]})
        if login_user:
            # check if password is correct
            if bcrypt.hashpw(request.form['pass'].encode('utf-8'), login_user['password']) == login_user['password']:
                session['username'] = request.form['username']
                session['logged_in'] = True
                return redirect(url_for('index'))
            error = "Invalid username or password"
        else:
            error = "Invalid username or password"

    return render_template("login.html", error=error)

@app.route("/register", methods=["POST", "GET"])
def register():
    error = None
    if request.method == "POST":
        if request.form["username"] != "":
            existing_user = db.findOne("users", {"username": request.form["username"]})
            # if username is not in db, create new user
            if existing_user is None:
                hashpass = bcrypt.hashpw(request.form["pass"].encode("utf-8"), bcrypt.gensalt())
                db.insert("users", {"username": request.form["username"], "password": hashpass})
                session["username"] = request.form["username"]
                session['logged_in'] = True
                return redirect(url_for("index"))
            error = "The username already exists" 
        else:
            error = "Invalid username"  
    
    return render_template("register.html", error=error)

@app.route("/logout")
def logout():
    session.pop('logged_in', None)
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.secret_key = "secretkey"
    app.run(host="localhost", port=4000, debug=True)
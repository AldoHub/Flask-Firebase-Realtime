from functools import wraps
import sys
import os
from flask import Flask, render_template, redirect, request, url_for, session
#coming from pyrebase4
import pyrebase

#firebase config
config = {
  
}

#init firebase
firebase = pyrebase.initialize_app(config)
#auth instance
auth = firebase.auth()
#real time database instance
db = firebase.database();


#new instance of Flask
app = Flask(__name__)
#secret key for the session
app.secret_key = os.urandom(24)

#decorator to protect routes
def isAuthenticated(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        #check for the variable that pyrebase creates
        if not auth.current_user != None:
            return redirect(url_for('signup'))
        return f(*args, **kwargs)
    return decorated_function

#index route
@app.route("/")
def index():
    allposts = db.child("Posts").get()
    #print(allposts.val(), file=sys.stderr)
    if allposts.val() == None:
      #print(posts, file=sys.stderr)
      return render_template("index.html")
    else:
      return render_template("index.html", posts=allposts)

#signup route
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
      #get the request form data
      email = request.form["email"]
      password = request.form["password"]
      try:
        #create the user
        auth.create_user_with_email_and_password(email, password);
        #login the user right away
        user = auth.sign_in_with_email_and_password(email, password)   
        #session
        user_id = user['idToken']
        user_email = email
        session['usr'] = user_id
        session["email"] = user_email
        return redirect("/") 
      except:
        return render_template("login.html", message="The email is already taken, try another one, please" )  

    return render_template("signup.html")


#login route
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
      #get the request data
      email = request.form["email"]
      password = request.form["password"]
      try:
        #login the user
        user = auth.sign_in_with_email_and_password(email, password)
        #set the session
        user_id = user['idToken']
        user_email = email
        session['usr'] = user_id
        session["email"] = user_email
        return redirect("/")  
      
      except:
        return render_template("login.html", message="Wrong Credentials" )  

     
    return render_template("login.html")

#logout route
@app.route("/logout")
def logout():
    #remove the token setting the user to None
    auth.current_user = None
    #also remove the session
    #session['usr'] = ""
    #session["email"] = ""
    session.clear()
    return redirect("/");

#create form
@app.route("/create", methods=["GET", "POST"])
@isAuthenticated
def create():
 
  if request.method == "POST":
    #get the request data
    title = request.form["title"]
    content = request.form["content"]

    post = {
      "title": title,
      "content": content,
      "author": session["email"]
    }

    try:
      #print(title, content, file=sys.stderr)

      #push the post object to the database
      db.child("Posts").push(post)
      return redirect("/")
    except:
      return render_template("create.html", message= "Something wrong happened")  

  return render_template("create.html")


@app.route("/post/<id>")
@isAuthenticated
def post(id):
    orderedDict = db.child("Posts").order_by_key().equal_to(id).limit_to_first(1).get()
    print(orderedDict, file=sys.stderr)
        
    return render_template("post.html", data=orderedDict)

@app.route("/edit/<id>", methods=["GET", "POST"])
def edit(id):
    if request.method == "POST":

      title = request.form["title"]
      content = request.form["content"]

      post = {
        "title": title,
        "content": content,
        "author": session["email"]
      }

      #update the post
      db.child("Posts").child(id).update(post)
      return redirect("/post/" + id) 
    
    
    orderedDict =  db.child("Posts").order_by_key().equal_to(id).limit_to_first(1).get()
    return render_template("edit.html", data=orderedDict)

@app.route("/delete/<id>", methods=["POST"])
def delete(id):
    db.child("Posts").child(id).remove()
    return redirect("/")


#run the main script
if __name__ == "__main__":
    app.run(debug=True)

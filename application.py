#!/usr/bin/python3

import os

from flask import Flask, session, render_template, url_for, request, flash, redirect, jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from werkzeug.security import check_password_hash, generate_password_hash
from functools import wraps

import requests

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

#DATABASE_URL = postgres://epzqwkivmgzdoz:f9fa4895d9117458edb0253623c4c1491c431587d3f822288fa1b73d485e93f2@ec2-79-125-110-209.eu-west-1.compute.amazonaws.com:5432/df0jghboock9u9

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

""" 
db.execute("CREATE DATABASE kutub")

db.execute("CREATE TABLE users \
             (id SERIAL PRIMARY KEY, \
              username VARCHAR UNIQUE NOT NULL, \
              password VARCHAR NOT NULL)")
  
db.execute("CREATE TABLE books \
              (ISBN VARCHAR PRIMARY KEY, \
               title VARCHAR NOT NULL, \
               author VARCHAR NOT NULL, \
               year INTEGER NOT NULL)")
  
db.execute("CREATE TABLE reviews \
              (id SERIAL PRIMARY KEY, \
               book_id VARCHAR REFERENCES books, \
               rating INTEGER NOT NULL, \
               opinion VARCHAR NOT NULL)")
  
db.execute("CREATE TABLE reviewers \
              (review_id INTEGER REFERENCES reviews, \
               user_id INTEGER REFERENCES users)")
  
db.execute("CREATE INDEX title_id ON books(title)") """

def login_required(f):
    """ Decorate routes to require login. """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/signin")
        return f(*args, **kwargs)
    return decorated_function
  

@app.route("/")
def index():
  return render_template("index.html")
  
  
@app.route("/signin", methods=["GET", "POST"])
def signin():
  if request.method == "POST":
    
    if not request.form.get("username"):
      return render_template("error.html", message="Must provide username")

    elif not request.form.get("password"):
      return render_template("error.html", message="Must provide password")
    
    checking = db.execute("SELECT * FROM users WHERE username = :username", {"username":request.form.get("username")}).fetchone()
    if checking == None or not check_password_hash(str(checking["password"]), request.form.get("password")):
      return render_template("error.html", message="Invalid username and/or password")
    
    session["user_id"] = checking["id"]
    
    return render_template("search.html")
  else:  
    return render_template("signin.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
  if request.method == "POST":
    
    if not request.form.get("username"):
      return render_template("error.html", message="Missing username")

    elif not request.form.get("password"):
      return render_template("error.html", message="Missing password")
    elif request.form.get("confirm") != request.form.get("password"):
      return render_template("error.html", message="Passwords do not match!")
      
    password = generate_password_hash(request.form.get("password"))
    username = request.form.get("username")
    
    exist = db.execute("SELECT * FROM users WHERE username=:username", {"username":username}).fetchone()
    print(exist)
    if exist:
      return render_template("error.html", message="User with this username already exist")
    
    db.execute("INSERT INTO users (username, password) VALUES(:username, :password)", {"username":username, "password":password})
    
    db.commit()
    session["user_id"] = username
    return render_template("search.html")
  else:
    return render_template("signup.html")


@app.route("/logout")
def logout():
  """Log user out"""

  session.clear()

  return redirect("/")
  
  
@app.route("/search", methods=["GET", "POST"])
@login_required
def search():
  if request.method == "POST":
    query = "%" + request.form.get("search") + "%"
    results = db.execute("SELECT * FROM books WHERE isbn LIKE :query \
                      OR title LIKE :query OR author like :query",
                      {"query":query}).fetchall()
    if db.execute("SELECT * FROM books WHERE isbn LIKE :query \
                      OR title LIKE :query OR author like :query",
                      {"query":query}).rowcount == 0:
      return render_template("error.html", message="Query reports no results")
    else:
      return render_template("results.html", results=results)

  else:
      return render_template("search.html")

@app.route("/book/<isbn>")
@login_required
def book(isbn):
  
  result = db.execute("SELECT * FROM books WHERE isbn=:isbn",{"isbn":isbn}).fetchone()

  if db.execute("SELECT * FROM books WHERE isbn=:isbn",{"isbn":isbn}).rowcount == 0:
    return render_template("error.html", message="Query reports no results")

  reviews = db.execute("SELECT avg(rating) AS avg, opinion FROM reviews WHERE book_id=:book_id GROUP BY opinion",{"book_id":isbn}).fetchall()

  goodreads = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "7OFw9iX4NiYcQRjI8uGCQ", "isbns": isbn}).json()
  
  print(reviews)

  return render_template("book.html", result=result, reviews=reviews, goodreads=goodreads)
  
@app.route("/review/<isbn>", methods=["POST"])
@login_required
def review(isbn):  
  if request.method == "POST":
    opinion = request.form.get("review")
    rating = int(request.form.get("rating"))
    
    exist =  db.execute("SELECT * FROM reviewers WHERE review_id in(SELECT id FROM reviews WHERE book_id=:isbn) AND user_id=:user_id", {"isbn": isbn, "user_id": session["user_id"]}).fetchone()
   
    
    if exist:
      return render_template("error.html", message="You have already left a review for this book. You can not leave more than one review per book.")
    
    review_id = db.execute("INSERT INTO reviews (book_id, rating, opinion) VALUES(:book_id, :rating, :opinion) RETURNING id", {"book_id": isbn, "rating": rating, "opinion": opinion}).fetchone()[0]
    
    db.execute("INSERT INTO reviewers (review_id, user_id) VALUES(:review_id, :user_id)", {"review_id": review_id, "user_id": session["user_id"]})
    
    db.commit()
    
@app.route("/api/<isbn>")
def kutub_api(isbn):      
  book = db.execute("SELECT title, author, year, count(opinion) AS count, avg(rating) AS avg FROM books JOIN reviews ON books.ISBN=reviews.book_id WHERE ISBN=:isbn GROUP BY isbn", {"isbn":isbn}).fetchone()
  print(book)
  if book == None:
    return jsonify({"error": "Invalid ISBN"}), 404
  
  return jsonify({
    "title": book.title,
    "author": book.author,
    "year": book.year,
    "isbn": isbn,
    "review_count": int(book.count),
    "average_score": "{0:.1f}".format(book.avg)
    #f'{book.avg:.1f}'
  })
  
if __name__ == "__main__":
  main()

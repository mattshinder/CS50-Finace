from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_session import Session
from passlib.apps import custom_app_context as pwd_context
from tempfile import mkdtemp
import re

from helpers import *

app = Flask(__name__)

if app.config["DEBUG"]:
    @app.after_request
    def after_request(response):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Expires"] = 0
        response.headers["Pragma"] = "no-cache"
        return response

app.jinja_env.filters["usd"] = usd

# configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

@app.route("/")
@login_required
def index():
    stocks=db.execute("SELECT * FROM stocks WHERE user_id=:id", id=session["user_id"])
    cash=db.execute("SELECT cash FROM users WHERE id=:id", id=session["user_id"])[0]["cash"]
    for stock in stocks:
        stock['total']=stock['price']*stock['number']
    return render_template("index.html", stocks=stocks, cash=cash)

@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    if request.method == "GET":
        return render_template("buy.html")
    if lookup(request.form.get("symbol"))== None:
        return apology("Invalid Company")
    if int(request.form.get("shares")) > 0:
        cash=db.execute("SELECT cash FROM users WHERE id=:id", id=session["user_id"])
        quote=lookup(request.form.get("symbol"))
        db.execute("INSERT into stocks(user_id,symbol,price,number) VALUES(:user_id,:symbol,:price,:number)", user_id=session["user_id"], symbol=quote["symbol"], price=float(quote["price"]), number=int(request.form.get("shares")))
        if cash[0]["cash"] < float(quote["price"])*int(request.form.get("shares")):
            return apology("Invalid Balance")
        db.execute("UPDATE users SET cash = cash - :price*:number WHERE id=:id", price=float(quote["price"]), id=session["user_id"], number=int(request.form.get("shares")))
        return redirect(url_for("index"))
    else:
        return apology("Invalid number of shares")
      
@app.route("/history")
@login_required
def history():
    """Show history of transactions."""
    return apology("TODO")

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in."""

    # forget any user_id
    session.clear()

    # if user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username")

        # ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password")

        # query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username", username=request.form.get("username"))

        # ensure username exists and password is correct
        if len(rows) != 1 or not pwd_context.verify(request.form.get("password"), rows[0]["hash"]):
            return apology("invalid username and/or password")

        # remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # redirect user to home page
        return redirect(url_for("index"))

    # else if user reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    """Log user out."""

    # forget any user_id
    session.clear()

    # redirect user to login form
    return redirect(url_for("login"))

@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    if request.method == "GET":
      return render_template("quote.html")
    if lookup(request.form.get("symbol"))== None:
      return apology("Invalid Company")
    
    else:
        return render_template("quoted.html", quote=lookup(request.form.get("symbol")))

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        if not request.form.get("username"):
            return apology("Sorry, but you have no username")
        
        elif not request.form.get("password"):
            return apology("must create password")
            
        else:
            hash = pwd_context.hash(request.form.get("password"))
            result = db.execute("INSERT into users(username, hash) VALUES(:username, :hash)", 
                                username = request.form.get("username"),
                                hash = hash)
            if not result:
                return apology("Could not create user name. Already exists.")
                    
            # redirect to login screen after account creation
            return redirect(url_for("login"))
            
    else:
        return render_template("register.html")
    
@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    if request.method == "GET":
        return render_template("sell.html")
    if lookup(request.form.get("symbol"))== None:
        return apology("Invalid Company")
    if int(request.form.get("shares")) < 0:
        cash=db.execute("SELECT cash FROM users WHERE id=:id", id=session["user_id"])
        quote=lookup(request.form.get("symbol"))
        db.execute("INSERT into stocks(user_id,symbol,price,number) VALUES(:user_id,:symbol,:price,:number)", user_id=session["user_id"], symbol=quote["symbol"], price=float(quote["price"]), number=int(request.form.get("shares")))
        db.execute("UPDATE users SET cash = cash - :price*:number WHERE id=:id", price=float(quote["price"]), id=session["user_id"], number=int(request.form.get("shares")))
        return redirect(url_for("index"))
    else:
        return apology("Invalid number of shares")
        
        
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
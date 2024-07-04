from flask import Flask, render_template, request, redirect, flash, session, jsonify
from polygon_api import P_get_annual_returns_in_dividends, P_get_company_logo, P_get_ticker_by_name, P_get_current_price, P_get_name
from alpha_vantage_api import AV_get_dividends_for_year, AV_get_current_price, AV_get_name, AV_get_ticker_by_name
from flask_session import Session
from helpers import usd, init_db, DataBase, login_required
from werkzeug.security import check_password_hash, generate_password_hash
import json
import os

app = Flask(__name__)

db = init_db("stock_valuation.db")

app.jinja_env.filters["usd"] = usd

app.secret_key = os.getenv("SECRET_KEY")

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
def index():
    if session.get("username"):
        username = session["username"]
        flash(f"Welcome to stock valuation {username}!")
    return render_template("index.html")

@app.route("/calculator", methods=["POST", "GET"])
def calculator():
    if request.method == "POST":

        dividends = []
        current_price = 0 

        for key, value in request.form.items():

            if "year" in key:
                dividends.append(float(value))
            elif "current_price" in key:
                current_price = float(value)

        all_returns = sum(dividends)
        years = len(dividends)
        
        annual_average = all_returns / years

        annual_percentage = (annual_average / current_price) * 100

        cap_price = annual_average / 0.06

        if annual_percentage >= 6:
            class_name = "return-high"
        elif annual_percentage >= 5.5 and annual_percentage <= 6:
            class_name = "return-medium"
        elif annual_percentage <= 5.4:
            class_name = "return-low"

        stock = {
            'name': "Calculated Stock",
            'price': usd(current_price),
            'annual_return': usd(annual_average),
            'percentage': round(annual_percentage, 2),
            'cap_price': usd(cap_price),
        }

        user_id = session.get("user_id", 0)
        if user_id:
            db.insert("search_history", user_id, stock)

        stock["class"] = class_name

        return render_template("stock_valuation.html", stock=stock)
    
    return render_template("calculator.html")

@app.route("/get_annual_returns", methods=["GET", "POST"])
def get_annual_returns():
    if request.method == "POST":
        stock = {}
        db = DataBase("stock_valuation.db")

        symbol_or_name = request.form.get("symbol")
        symbol = P_get_ticker_by_name(symbol_or_name)
        if not symbol:
            symbol = symbol_or_name.upper()

        result = P_get_annual_returns_in_dividends(symbol=symbol)
        if result is None:
            average_annual_returns, returns = None, None
        else:
            average_annual_returns, returns = result

        if average_annual_returns is None and returns is None:
            result = AV_get_dividends_for_year(symbol)
            if result is None:
                average_annual_returns, returns = None, None
                print("Unable to find requested symbol with Polygon Api and Alpha")
                flash("Unable to find requested symbol with Polygon Api and Alpha")
                return render_template("index.html")
            

        dividends_by_year = {}
        for record in returns:
            for year, dividend in record.items():
                if year in dividends_by_year:
                    dividends_by_year[year] += dividend
                else:
                    dividends_by_year[year] = dividend
                


        cap_price = (average_annual_returns / 0.06) 
        name = P_get_name(symbol)
        price = AV_get_current_price(symbol)
        if not price:
            price = P_get_current_price(symbol)

        percentage = (average_annual_returns / price) * 100

        if percentage >= 6:
            class_name = "return-high"
        elif percentage >= 5.5 and percentage <= 6:
            class_name = "return-medium"
        elif percentage <= 5.4:
            class_name = "return-low"

        stock = {
            'name': name,
            'price': usd(price),
            'annual_return': usd(average_annual_returns),
            'percentage': round(percentage, 2),
            'cap_price': usd(cap_price),
            'dividends_history': dividends_by_year,
        }
        user_id = session.get("user_id", 0)
        if user_id:
            db.insert("search_history", user_id, stock)

        stock["class"] = class_name
        return render_template("stock_valuation.html", stock=stock)

    return render_template("index.html")


@app.route("/search-history")
def search_history():

    user_id = session.get("user_id", 0)
    if not user_id:
        flash("Access Forbidden: Users must Sign In to access Search History")
        return render_template("index.html")
    
    db = DataBase("stock_valuation.db")

    stocks = db.selectall("search_history", ["name", "cap_price", "price", "annual_return", "percentage", "dividends_history", "datetime"],
                           {"user_id": user_id})

    stocks_list = []

    for stock in stocks:
        dict = {
            "name": stock[0],
            "cap_price": stock[1],
            "price": stock[2],
            "annual_return": stock[3],
            "percentage": stock[4],
            "dividends_history": json.loads(stock[5]),
            "datetime": stock[6]
        }
        stocks_list.append(dict)

    consolidated_stocks = {}

    for stock in stocks_list:
        name = stock["name"]
        if name in consolidated_stocks:
            consolidated_stocks[name]["times_searched"] += 1
            consolidated_stocks[name]["datetimes"].append(stock["datetime"])
        else:
            consolidated_stocks[name] = {
                "name": stock["name"],
                "cap_price": stock["cap_price"],
                "price": stock["price"],
                "annual_return": stock["annual_return"],
                "percentage": stock["percentage"],
                "dividends_history": stock["dividends_history"],
                "times_searched": 1,
                "datetimes": [stock["datetime"]]
            }

    consolidated_stocks_list = list(consolidated_stocks.values())

    for record in consolidated_stocks_list:
        for year, dividend in record['dividends_history'].items():
                record['dividends_history'][year] = usd(dividend)

    session["stock_data"] = consolidated_stocks_list

    names = [cs["name"] for cs in consolidated_stocks_list]
    
    return render_template("history.html", names=names)


@app.route("/history-data")
def history_data():
    stocks = session.get("stock_data", 0)
    name = request.args.get("name")

    stock = {}

    for s in stocks:
        if name in s['name']:
            stock = s
    
    return jsonify(stock)


@app.route("/register", methods=["GET", "POST"])
def register():
   
    if request.method == "POST":

        db = DataBase("stock_valuation.db")

        new_username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        if new_username == "" or password == "" or confirmation == "":
            flash("You must fill all fields in this form")
            return render_template("register.html")
        
        if password != confirmation:
            flash("Password and confirmation not identical")
            return render_template("register.html")
        confirmation = ""

        row = db.select("users", ["username"], {"username": new_username})
        if row:
            flash("Username already taken")
            return render_template("register.html")

        hash = generate_password_hash(password)
        db.add("users", {"username": new_username, "password": hash})
        row = db.select("users", ["id"], {"username": new_username})
        session["user_id"] = row[0]

        return redirect("/")


    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    session.clear()

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if not password or not username:
            flash("You must fill the fields of username and password")
            return render_template("login.html")
        
        db = DataBase("stock_valuation.db")
        row = db.select("users", ["id", "password"], {"username": username})
        db.close_connection()
        if len(row) < 1:
            flash("Invalid username or password")
            return render_template("login.html")
        
        user_id = row[0]
        hash = row[1]
        if check_password_hash(password, hash):
            session["user_id"] = user_id
            session["username"] = username

            return redirect("/")


    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    """Log user out"""

    session.clear()

    return redirect("/")

@app.route("/get_names", methods=["GET"])
def get_names():

    input = request.args.get("input")

    list_of_names = P_get_ticker_by_name(input)


    if not list_of_names:
        jsonify({"error": "Symbol parameter is missing"}), 400

    return jsonify({'list_of_names': list_of_names}), 200



if __name__ == '__main__':
    app.run(debug=True)


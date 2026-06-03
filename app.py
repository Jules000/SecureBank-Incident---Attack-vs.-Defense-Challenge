import os
import sqlite3
import hashlib
from datetime import datetime
from flask import Flask, render_template, request, session, redirect, url_for

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database", "db.sqlite")

app = Flask(__name__)
app.secret_key = "bank_secret"


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def hash_password(password):
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")

        try:
            conn = get_db()
            cur = conn.cursor()
            query = f"SELECT * FROM users WHERE username = '{username}'"
            cur.execute(query)
            user = cur.fetchone()
            conn.close()

            if user:
                hashed_input = hash_password(password)
                if user["password"] == hashed_input:
                    session["username"] = user["username"]
                    session["user_name"] = user["name"]
                    session["balance"] = user["balance"]
                    return redirect(url_for("dashboard"))
                else:
                    error = "Invalid credentials"
            else:
                error = "Invalid credentials"
        except Exception as e:
            error = f"Database error: {e}"

    return render_template("login.html", error=error)


@app.route("/dashboard")
def dashboard():
    if "user_name" not in session:
        return redirect(url_for("login"))
    name = session["user_name"]
    username = session.get("username", "user")
    initials = "".join(part[0].upper() for part in name.split() if part)
    profile_image = f"/static/images/profiles/{username}.png"

    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "SELECT description, category, date, amount, type FROM transactions WHERE user_id = (SELECT id FROM users WHERE username = ?) ORDER BY date DESC",
        (username,),
    )
    transactions = [dict(row) for row in cur.fetchall()]
    conn.close()

    for txn in transactions:
        raw = txn["date"]
        try:
            dt = datetime.strptime(raw, "%Y-%m-%d")
            txn["date"] = dt.strftime("%b %d, %Y")
        except ValueError:
            pass

    CATEGORY_ICONS = {
        "technology": "shopping_cart",
        "dining": "restaurant",
        "income": "payments",
        "shopping": "shopping_bag",
        "transport": "directions_car",
        "entertainment": "movie",
        "health": "local_hospital",
        "utilities": "bolt",
        "transfer": "swap_horiz",
        "withdrawal": "money_off",
    }

    return render_template(
        "dashboard.html",
        user_name=name,
        user_initials=initials,
        profile_image=profile_image,
        balance=f"${session['balance']:,.2f}",
        transactions=transactions,
        category_icons=CATEGORY_ICONS,
    )


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)

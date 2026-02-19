import pickle
import sqlite3
import numpy as np
import os
import math

from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from feature_extraction import extract_features

# ---------------- APP CONFIG ----------------
app = Flask(__name__)
app.secret_key = "super_secret_key_change_later"

# ---------------- LOAD ML MODEL ----------------
MODEL_PATH = os.path.join("model", "phishing_model.pkl")
with open(MODEL_PATH, "rb") as f:
    model = pickle.load(f)

# ---------------- DATABASE ----------------
def get_db():
    return sqlite3.connect("database.db")

def init_db():
    conn = get_db()
    cur = conn.cursor()

    # Users table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fullname TEXT,
            username TEXT UNIQUE,
            password TEXT
        )
    """)

    # History table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            url TEXT,
            prediction TEXT,
            confidence REAL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()

init_db()

# ---------------- SECURE ADMIN ROUTES ----------------

def admin_required():
    return ("role" in session) and (session["role"] == "admin")

# ---------------- AUTH ROUTES ----------------

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        fullname = request.form["fullname"]
        username = request.form["username"]
        password = request.form["password"]

        hashed_pw = generate_password_hash(password)

        try:
            conn = get_db()
            cur = conn.cursor()
            cur.execute(
    "INSERT INTO users (fullname, username, password, role, status) VALUES (?, ?, ?, 'user', 'pending')",
    (fullname, username, hashed_pw)
)

            conn.commit()
            conn.close()
            return redirect(url_for("login"))
        except:
            return render_template("signup.html", error="Username already exists")

    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username=?", (username,))
        user = cur.fetchone()
        conn.close()

        # ❌ USER NOT FOUND
        if not user:
            return render_template("login.html", error="Invalid username or password")

        # ❌ PASSWORD WRONG
        if not check_password_hash(user[3], password):
            return render_template("login.html", error="Invalid username or password")

        # ✅ USER EXISTS & PASSWORD OK
        role = user[4]
        status = user[5]

        if status == "pending":
            return render_template("login.html", error="Waiting for admin approval")

        if status == "blocked":
            return render_template("login.html", error="Your account is blocked by admin")

        session["user"] = username
        session["role"] = role

        if role == "admin":
            return redirect(url_for("admin_dashboard"))
        else:
            return redirect(url_for("home"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))

# ---------------- PROTECTED HOME ----------------

@app.route("/")
def home():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("index.html", user=session["user"])

# ---------------- PREDICTION ----------------

@app.route("/predict", methods=["POST"])
def predict():
    if "user" not in session:
        return redirect(url_for("login"))

    try:
        url = request.form.get("url", "").strip()
        if not url:
            return render_template("index.html", error="Please enter a URL.", user=session["user"])

        if not (url.startswith("http://") or url.startswith("https://")):
            url = "http://" + url

        features = extract_features(url)
        features_arr = np.array(features).reshape(1, -1)

        pred = model.predict(features_arr)[0]
        prob = model.predict_proba(features_arr)[0] if hasattr(model, "predict_proba") else None

        label_text = "Phishing Website — DO NOT TRUST" if pred == 1 else "Legitimate / Safe Website"

        confidence = None
        if prob is not None:
            confidence = round(float(prob[pred]) * 100, 2)

        # ---------- SAVE HISTORY (THIS WAS MISSING ❗) ----------
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO history (username, url, prediction, confidence) VALUES (?, ?, ?, ?)",
            (session["user"], url, label_text, confidence)
        )
        conn.commit()
        conn.close()

        return render_template(
            "result.html",
            url=url,
            prediction=label_text,
            confidence=confidence,
            user=session["user"]
        )

    except Exception as e:
        return render_template("index.html", error=str(e), user=session["user"])

# ---------------- HISTORY PAGE ----------------
@app.route('/history')
def history():
    if 'user' not in session:
        return redirect(url_for('login'))

    user = session['user']

    # Pagination settings
    page = request.args.get('page', 1, type=int)
    per_page = 5
    offset = (page - 1) * per_page

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # Get total records count
    cursor.execute("SELECT COUNT(*) FROM history WHERE username = ?", (user,))
    total_records = cursor.fetchone()[0]

    # Get only 5 records
    cursor.execute("""
        SELECT url, prediction, confidence, timestamp
        FROM history
        WHERE username = ?
        ORDER BY timestamp DESC
        LIMIT ? OFFSET ?
    """, (user, per_page, offset))

    records = cursor.fetchall()
    conn.close()

    total_pages = math.ceil(total_records / per_page)

    return render_template(
        'history.html',
        records=records,
        user=user,
        page=page,
        total_pages=total_pages
    )

@app.route("/admin")
def admin_dashboard():
    if "user" not in session:
        return redirect(url_for("login"))
    if not admin_required():
        return redirect(url_for("home"))

    conn = get_db()
    cur = conn.cursor()

    # Users
    cur.execute("SELECT id, fullname, username, role, status FROM users ORDER BY id DESC")
    users = cur.fetchall()

    # History (all users)
    cur.execute("""
        SELECT username, url, prediction, confidence, timestamp
        FROM history
        ORDER BY timestamp DESC
    """)
    history = cur.fetchall()

    # Stats
    cur.execute("SELECT COUNT(*) FROM users")
    total_users = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM history")
    total_checks = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM history WHERE prediction LIKE 'Phishing%'")
    phishing_count = cur.fetchone()[0]

    conn.close()

    return render_template(
        "admin.html",
        users=users,
        history=history,
        total_users=total_users,
        total_checks=total_checks,
        phishing_count=phishing_count,
        user=session["user"]
    )
@app.route("/admin/approve/<int:user_id>")
def approve_user(user_id):
    if not admin_required():
        return redirect(url_for("home"))

    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE users SET status='active' WHERE id=?", (user_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("admin_dashboard"))

#-------------BLOCK AND UNBLOCK USER------------------

@app.route("/admin/toggle_block/<int:user_id>")
def toggle_block(user_id):
    if not admin_required():
        return redirect(url_for("home"))

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT status FROM users WHERE id=?", (user_id,))
    status = cur.fetchone()[0]

    new_status = "blocked" if status != "blocked" else "active"
    cur.execute("UPDATE users SET status=? WHERE id=?", (new_status, user_id))
    conn.commit()
    conn.close()
    return redirect(url_for("admin_dashboard"))

#---------------USER-ADMIN---------------------
@app.route("/admin/toggle_role/<int:user_id>")
def toggle_role(user_id):
    if not admin_required():
        return redirect(url_for("home"))

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT role FROM users WHERE id=?", (user_id,))
    role = cur.fetchone()[0]

    new_role = "admin" if role == "user" else "user"
    cur.execute("UPDATE users SET role=? WHERE id=?", (new_role, user_id))
    conn.commit()
    conn.close()
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/users")
def manage_users():
    if "user" not in session or session.get("role") != "admin":
        return redirect(url_for("login"))

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, fullname, username, role, status FROM users")
    users = cur.fetchall()
    conn.close()

    return render_template("manage_users.html", users=users, user=session["user"])



@app.route("/admin/history")
def view_history():
    if "user" not in session or session.get("role") != "admin":
        return redirect(url_for("login"))

    conn = get_db()
    cur = conn.cursor()

    # Get page number from URL
    page = request.args.get("page", 1, type=int)
    per_page = 10
    offset = (page - 1) * per_page

    # Get total records
    cur.execute("SELECT COUNT(*) FROM history")
    total_records = cur.fetchone()[0]

    # Fetch 10 records only
    cur.execute("""
        SELECT username, url, prediction, confidence, timestamp
        FROM history
        ORDER BY timestamp DESC
        LIMIT ? OFFSET ?
    """, (per_page, offset))

    history = cur.fetchall()
    conn.close()

    total_pages = math.ceil(total_records / per_page)

    return render_template(
        "view_history.html",
        history=history,
        user=session["user"],
        page=page,
        total_pages=total_pages
    )


@app.route("/charts")
def charts():
    if "user" not in session:
        return redirect(url_for("login"))

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM history WHERE prediction LIKE 'Phishing%'")
    phishing_count = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM history WHERE prediction LIKE 'Legitimate%'")
    safe_count = cur.fetchone()[0]

    conn.close()

    return render_template(
        "charts.html",
        phishing_count=phishing_count,
        safe_count=safe_count,
        user=session["user"]
    )


# ---------------- RUN ----------------
#if __name__ == "__main__":
  #app.run(debug=True)
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

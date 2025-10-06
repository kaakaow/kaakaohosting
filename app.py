
from flask import Flask, render_template, request, redirect, url_for, session
import os, sqlite3

# --- ASETUKSET ---
app = Flask(__name__)
app.secret_key = "kaakaow_secret_key"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
DB_PATH = os.path.join(BASE_DIR, "database.db")

# --- KANSIOT ---
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(TEMPLATES_DIR, exist_ok=True)

# --- AUTOMAATTINEN TEMPLATES-LUONTI ---
login_html = os.path.join(TEMPLATES_DIR, "login.html")
panel_html = os.path.join(TEMPLATES_DIR, "panel.html")

if not os.path.exists(login_html):
    with open(login_html, "w") as f:
        f.write("""<!DOCTYPE html>
<html>
<head>
    <title>Kaakaow Hosting - Kirjaudu</title>
    <style>
        body { font-family: sans-serif; text-align: center; margin-top: 100px; background: #f5f6fa; }
        form { background: white; display: inline-block; padding: 30px; border-radius: 15px; box-shadow: 0 0 10px #ddd; }
        input { display: block; margin: 10px auto; padding: 10px; width: 80%; }
        button { padding: 10px 20px; background: #007bff; color: white; border: none; border-radius: 8px; cursor: pointer; }
        button:hover { background: #0056b3; }
        .error { color: red; }
    </style>
</head>
<body>
    <h2>Kaakaow Hosting</h2>
    <form method="POST">
        <input type="text" name="username" placeholder="Käyttäjätunnus" required>
        <input type="password" name="password" placeholder="Salasana" required>
        <button type="submit">Kirjaudu</button>
        {% if error %}<p class="error">{{ error }}</p>{% endif %}
    </form>
</body>
</html>""")

if not os.path.exists(panel_html):
    with open(panel_html, "w") as f:
        f.write("""<!DOCTYPE html>
<html>
<head>
    <title>Kaakaow Hosting - Paneeli</title>
    <style>
        body { font-family: sans-serif; background: #eef2f7; text-align: center; margin: 0; }
        header { background: #007bff; color: white; padding: 15px; font-size: 20px; }
        main { margin-top: 30px; }
        form { background: white; display: inline-block; padding: 20px; border-radius: 15px; box-shadow: 0 0 10px #ddd; }
        input, button { margin: 8px; padding: 10px; }
        table { margin: 30px auto; background: white; border-collapse: collapse; }
        td, th { border: 1px solid #ccc; padding: 8px 15px; }
        th { background: #f1f1f1; }
        .logout { float: right; color: white; text-decoration: none; }
    </style>
</head>
<body>
    <header>
        Kaakaow Hosting - Paneeli
        <a href="/logout" class="logout">Kirjaudu ulos</a>
    </header>
    <main>
        <form method="POST" enctype="multipart/form-data">
            <input type="text" name="servername" placeholder="Projektin nimi" required>
            <input type="file" name="file" required>
            <button type="submit">Lataa & Julkaise</button>
        </form>
        <h3>Omat sivut</h3>
        <table>
            <tr><th>Nimi</th><th>Tiedosto</th></tr>
            {% for s in servers %}
            <tr><td>{{ s['name'] }}</td><td>{{ s['path'] }}</td></tr>
            {% endfor %}
        </table>
    </main>
</body>
</html>""")

# --- TIETOKANTA ---
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# Luo tietokanta jos ei ole
with get_db() as db:
    db.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT)")
    db.execute("CREATE TABLE IF NOT EXISTS servers (id INTEGER PRIMARY KEY, user_id INTEGER, name TEXT, path TEXT)")

# --- ROUTET ---
@app.route("/")
def home():
    if "user" in session:
        return redirect(url_for("panel"))
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = request.form["username"]
        pw = request.form["password"]
        with get_db() as db:
            res = db.execute("SELECT * FROM users WHERE username=? AND password=?", (user, pw)).fetchone()
        if res:
            session["user"] = res["id"]
            return redirect(url_for("panel"))
        else:
            return render_template("login.html", error="Virheellinen tunnus tai salasana.")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))

@app.route("/panel", methods=["GET", "POST"])
def panel():
    if "user" not in session:
        return redirect(url_for("login"))

    user_id = session["user"]
    with get_db() as db:
        servers = db.execute("SELECT * FROM servers WHERE user_id=?", (user_id,)).fetchall()

    if request.method == "POST":
        name = request.form["servername"]
        file = request.files["file"]
        if name and file:
            save_path = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(save_path)
            with get_db() as db:
                db.execute("INSERT INTO servers (user_id, name, path) VALUES (?, ?, ?)", (user_id, name, save_path))
            return redirect(url_for("panel"))

    return render_template("panel.html", servers=servers)

# --- KÄYNNISTYS ---
if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=10000)

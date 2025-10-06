from flask import Flask, request, redirect, url_for, session
import os, sqlite3


app = Flask(__name__)
app.secret_key = "kaakaow_secret_key"
UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn

# Luo tietokanta jos ei ole
with get_db() as db:
    db.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT)")
    db.execute("CREATE TABLE IF NOT EXISTS servers (id INTEGER PRIMARY KEY, user_id INTEGER, name TEXT, path TEXT)")

@app.route("/")
def home():
    if "user" in session:
        return redirect(url_for("panel"))
    return redirect(url_for("login"))

# 🔹 Rekisteröityminen
@app.route("/register", methods=["GET", "POST"])
def register():
    html = """
    <h1>Rekisteröidy</h1>
    <form method='POST'>
        Käyttäjänimi:<br><input name='username'><br>
        Salasana:<br><input name='password' type='password'><br>
        <button type='submit'>Luo tili</button>
    </form>
    <p>Onko sinulla jo tili? <a href='/login'>Kirjaudu</a></p>
    """
    if request.method == "POST":
        user = request.form["username"]
        pw = request.form["password"]
        if not user or not pw:
            return html + "<p style='color:red;'>Täytä kaikki kentät!</p>"
        with get_db() as db:
            try:
                db.execute("INSERT INTO users (username, password) VALUES (?, ?)", (user, pw))
                db.commit()
                return redirect(url_for("login"))
            except sqlite3.IntegrityError:
                return html + "<p style='color:red;'>Käyttäjänimi on jo käytössä.</p>"
    return html

# 🔹 Kirjautuminen
@app.route("/login", methods=["GET", "POST"])
def login():
    html = """
    <h1>Kirjaudu sisään</h1>
    <form method='POST'>
        Käyttäjänimi:<br><input name='username'><br>
        Salasana:<br><input name='password' type='password'><br>
        <button type='submit'>Kirjaudu</button>
    </form>
    <p>Ei tiliä? <a href='/register'>Luo uusi</a></p>
    """
    if request.method == "POST":
        user = request.form["username"]
        pw = request.form["password"]
        with get_db() as db:
            res = db.execute("SELECT * FROM users WHERE username=? AND password=?", (user, pw)).fetchone()
        if res:
            session["user"] = res["id"]
            return redirect(url_for("panel"))
        else:
            return html + "<p style='color:red;'>Virheellinen tunnus tai salasana.</p>"
    return html

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))

# 🔹 Paneeli
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

    server_list = "".join([f"<li>{s['name']} — {s['path']}</li>" for s in servers])

    html = f"""
    <h1>KaakaoHosting - Hallintapaneeli</h1>
    <p><a href='/logout'>Kirjaudu ulos</a></p>
    <form method='POST' enctype='multipart/form-data'>
        Palvelimen nimi:<br><input name='servername'><br>
        Tiedosto:<br><input type='file' name='file'><br>
        <button type='submit'>Tallenna</button>
    </form>
    <h2>Omat palvelimet</h2>
    <ul>{server_list if server_list else "<i>Ei palvelimia</i>"}</ul>
    """
    return html

if __name__ == "__main__":
    app.run(debug=True)


from flask import Flask, render_template, request, redirect, session, send_file
import sqlite3
import random
import smtplib
from email.mime.text import MIMEText
from werkzeug.security import generate_password_hash, check_password_hash
import matplotlib.pyplot as plt
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import A4

app = Flask(__name__)
app.config['SECRET_KEY'] = "supersecret"

# ---------------- DATABASE ----------------
def init_db():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            note INTEGER
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT,
            prenom TEXT,
            email TEXT UNIQUE,
            password TEXT,
            role TEXT,
            verified INTEGER DEFAULT 0,
            code TEXT
        )
    """)

    conn.commit()
    conn.close()

init_db()

# ---------------- EMAIL FUNCTION ----------------
def send_code(email, code):
    sender = "tonemail@gmail.com"
    password = "mot_de_passe_application"

    message = MIMEText(f"Votre code de verification est : {code}")
    message["Subject"] = "Verification E-CERPAMAD"
    message["From"] = sender
    message["To"] = email

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(sender, password)
    server.sendmail(sender, email, message.as_string())
    server.quit()

# ---------------- REGISTER ----------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        nom = request.form["nom"]
        prenom = request.form["prenom"]
        email = request.form["email"]
        password = generate_password_hash(request.form["password"])

        conn = sqlite3.connect("database.db")
        c = conn.cursor()

        # Limite à 4 admins
        c.execute("SELECT COUNT(*) FROM users WHERE role='admin'")
        admin_count = c.fetchone()[0]

        if admin_count < 4:
            role = "admin"
        else:
            role = "etudiant"

        code = str(random.randint(100000, 999999))

        try:
            c.execute("""
                INSERT INTO users (nom, prenom, email, password, role, code)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (nom, prenom, email, password, role, code))

            conn.commit()
            conn.close()

            send_code(email, code)
            return redirect(f"/verify/{email}")

        except:
            return "Email déjà utilisé ❌"

    return render_template("register.html")

# ---------------- VERIFY ----------------
@app.route("/verify/<email>", methods=["GET", "POST"])
def verify(email):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    if request.method == "POST":
        code = request.form["code"]

        c.execute("SELECT code FROM users WHERE email=?", (email,))
        db_code = c.fetchone()[0]

        if code == db_code:
            c.execute("UPDATE users SET verified=1 WHERE email=?", (email,))
            conn.commit()
            conn.close()
            return redirect("/login")
        else:
            return "Code incorrect ❌"

    conn.close()
    return render_template("verify.html", email=email)

# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute("SELECT password, role, verified FROM users WHERE email=?", (email,))
        user = c.fetchone()
        conn.close()

        if user and check_password_hash(user[0], password):
            if user[2] == 0:
                return "Veuillez verifier votre email ❌"

            session["user"] = email
            session["role"] = user[1]
            return redirect("/")
        else:
            return "Identifiants incorrects ❌"

    return render_template("login.html")

# ---------------- DASHBOARD ----------------
@app.route("/")
def dashboard():
    if "user" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT * FROM students")
    students = c.fetchall()
    conn.close()

    return render_template("dashboard.html", students=students)

# ---------------- ADD STUDENT ----------------
@app.route("/add", methods=["POST"])
def add():
    if session.get("role") != "admin":
        return "Accès refusé ❌"

    name = request.form["name"]
    note = request.form["note"]

    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("INSERT INTO students (name, note) VALUES (?, ?)", (name, note))
    conn.commit()
    conn.close()

    return redirect("/")

# ---------------- GRAPH ----------------
@app.route("/graph")
def graph():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT name, note FROM students")
    data = c.fetchall()
    conn.close()

    names = [x[0] for x in data]
    notes = [x[1] for x in data]

    plt.figure()
    plt.bar(names, notes)
    plt.savefig("static/graph.png")
    plt.close()

    return redirect("/")

# ---------------- PDF ----------------
@app.route("/pdf")
def pdf():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT name, note FROM students")
    data = c.fetchall()
    conn.close()

    file_path = "resultats.pdf"
    doc = SimpleDocTemplate(file_path, pagesize=A4)
    elements = []

    style = ParagraphStyle(name='Normal', fontSize=12, textColor=colors.black)

    elements.append(Paragraph("Resultats des Etudiants", style))
    elements.append(Spacer(1, 0.5 * inch))

    for student in data:
        elements.append(Paragraph(f"{student[0]} : {student[1]}", style))
        elements.append(Spacer(1, 0.2 * inch))

    doc.build(elements)

    return send_file(file_path, as_attachment=True)

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

if __name__ == "__main__":
    app.run(debug=True)

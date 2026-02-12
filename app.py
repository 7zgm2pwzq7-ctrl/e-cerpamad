from flask import Flask, render_template, request, redirect, session, send_file
import sqlite3
import matplotlib.pyplot as plt
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import A4
import os

app = Flask(__name__)
app.secret_key = "supersecretkey"

# -------- DATABASE INIT --------
def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            note INTEGER
        )
    """)
    conn.commit()
    conn.close()

init_db()

# -------- HOME --------
@app.route("/")
def home():
    if "admin" in session:
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM students")
        students = cursor.fetchall()
        conn.close()
        return render_template("dashboard.html", students=students)
    return redirect("/login")

# -------- LOGIN --------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form["username"] == "admin" and request.form["password"] == "1234":
            session["admin"] = "admin"
            return redirect("/")
        else:
            return "Identifiants incorrects ❌"
    return render_template("login.html")

# -------- LOGOUT --------
@app.route("/logout")
def logout():
    session.pop("admin", None)
    return redirect("/login")

# -------- ADD STUDENT --------
@app.route("/add", methods=["POST"])
def add():
    name = request.form["name"]
    note = request.form["note"]
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO students (name, note) VALUES (?, ?)", (name, note))
    conn.commit()
    conn.close()
    return redirect("/")

# -------- GRAPH --------
@app.route("/graph")
def graph():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT name, note FROM students")
    data = cursor.fetchall()
    conn.close()

    names = [x[0] for x in data]
    notes = [x[1] for x in data]

    plt.figure()
    plt.bar(names, notes)
    plt.xlabel("Etudiants")
    plt.ylabel("Notes")
    plt.title("Graphique des Notes")
    plt.savefig("static/graph.png")
    plt.close()

    return redirect("/")

# -------- PDF --------
@app.route("/pdf")
def generate_pdf():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT name, note FROM students")
    data = cursor.fetchall()
    conn.close()

    file_path = "resultats.pdf"
    doc = SimpleDocTemplate(file_path, pagesize=A4)
    elements = []

    style = ParagraphStyle(
        name='Normal',
        fontSize=12,
        textColor=colors.black
    )

    elements.append(Paragraph("Resultats des Etudiants", style))
    elements.append(Spacer(1, 0.5 * inch))

    for student in data:
        elements.append(Paragraph(f"{student[0]} : {student[1]}", style))
        elements.append(Spacer(1, 0.2 * inch))

    doc.build(elements)

    return send_file(file_path, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)

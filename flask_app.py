from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_strong_secret_key'

# Create uploads folder if it doesn't exist
if not os.path.exists('uploads'):
    os.makedirs('uploads')

# --- Initialize database ---
def init_db():
    conn = sqlite3.connect('students.db')
    c = conn.cursor()

    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL
                 )''')

    # Classes table
    c.execute('''CREATE TABLE IF NOT EXISTS classes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    module TEXT NOT NULL,
                    link TEXT NOT NULL
                 )''')

    # Submissions table
    c.execute('''CREATE TABLE IF NOT EXISTS submissions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_name TEXT NOT NULL,
                    module TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    submitted_at TEXT NOT NULL
                 )''')

    # Insert 9 modules if empty
    c.execute("SELECT COUNT(*) FROM classes")
    if c.fetchone()[0] == 0:
        example_classes = [
            ('Module 1: Introduction', 'http://meet.google.com/ocm-svpm-bvh'),
            ('Module 2: Design Elements', 'http://meet.google.com/ocm-svpm-bvh'),
            ('Module 3: Color Theory', 'http://meet.google.com/ocm-svpm-bvh'),
            ('Module 4: Typography', 'http://meet.google.com/ocm-svpm-bvh'),
            ('Module 5: Layout & Composition', 'http://meet.google.com/ocm-svpm-bvh'),
            ('Module 6: Branding & Logo Design', 'http://meet.google.com/ocm-svpm-bvh'),
            ('Module 7: Poster & Flyer Design', 'http://meet.google.com/ocm-svpm-bvh'),
            ('Module 8: Social Media Graphics', 'http://meet.google.com/ocm-svpm-bvh'),
            ('Module 9: Final Project', 'http://meet.google.com/ocm-svpm-bvh'),
        ]
        c.executemany("INSERT INTO classes (module, link) VALUES (?, ?)", example_classes)

    conn.commit()
    conn.close()

init_db()

# --- Routes ---
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        try:
            conn = sqlite3.connect('students.db')
            c = conn.cursor()
            c.execute("INSERT INTO users (email, password) VALUES (?,?)", (email, password))
            conn.commit()
            conn.close()
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            return "Email already exists"
    return render_template('register.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        conn = sqlite3.connect('students.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE email=?", (email,))
        user = c.fetchone()
        conn.close()
        if user and check_password_hash(user[2], password):
            session['user'] = user[1]
            return redirect(url_for('dashboard'))
        else:
            return "Invalid credentials"
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))

    conn = sqlite3.connect('students.db')
    c = conn.cursor()
    c.execute("SELECT module, link FROM classes")
    classes = c.fetchall()

    c.execute("SELECT student_name, module, filename, submitted_at FROM submissions")
    submissions = c.fetchall()
    conn.close()

    return render_template('dashboard.html', user=session['user'], classes=classes, submissions=submissions)

@app.route('/upload', methods=['GET','POST'])
def upload():
    if 'user' not in session:
        return redirect(url_for('login'))

    conn = sqlite3.connect('students.db')
    c = conn.cursor()
    c.execute("SELECT module FROM classes")
    modules = c.fetchall()
    conn.close()

    if request.method == 'POST':
        student_name = request.form['student_name']
        module = request.form['module']
        file = request.files['assignment_file']
        filename = file.filename
        file.save(f'uploads/{filename}')

        conn = sqlite3.connect('students.db')
        c = conn.cursor()
        c.execute("INSERT INTO submissions (student_name, module, filename, submitted_at) VALUES (?,?,?,?)",
                  (student_name, module, filename, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        conn.close()
        return "Assignment submitted successfully!"

    return render_template('upload.html', modules=modules)

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

from flask import Flask, jsonify, render_template, request
import sqlite3
import os

app = Flask(__name__)

# Use in-memory database for Vercel (read-only filesystem workaround)
def get_db():
    # Create a connection to an in-memory database
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    # Create tables
    conn.execute('CREATE TABLE cities (id INTEGER PRIMARY KEY, name TEXT)')
    conn.execute('CREATE TABLE classes (id INTEGER PRIMARY KEY, city_id INTEGER, name TEXT)')
    conn.execute('CREATE TABLE students (id INTEGER PRIMARY KEY, name TEXT, city_id INTEGER, class_id INTEGER, total_points INTEGER)')
    
    # Insert sample data
    conn.execute("INSERT INTO cities VALUES (1, 'Madamod'), (2, 'المنشاة')")
    conn.execute("INSERT INTO classes VALUES (1, 1, 'Mathematics 101'), (2, 1, 'Physics 202'), (3, 2, 'الرياضيات')")
    conn.execute("INSERT INTO students VALUES (1, 'Test Student', 1, 1, 50), (2, 'طالب تجريبي', 2, 3, 75)")
    conn.commit()
    
    # Store the connection globally
    app.config['DB_CONN'] = conn

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/cities')
def get_cities():
    conn = app.config.get('DB_CONN')
    if not conn:
        init_db()
        conn = app.config['DB_CONN']
    cities = conn.execute('SELECT * FROM cities').fetchall()
    return jsonify([dict(c) for c in cities])

@app.route('/api/classes')
def get_classes():
    city_id = request.args.get('city_id', type=int)
    conn = app.config.get('DB_CONN')
    if not conn:
        init_db()
        conn = app.config['DB_CONN']
    if city_id:
        classes = conn.execute('SELECT * FROM classes WHERE city_id = ?', (city_id,)).fetchall()
    else:
        classes = conn.execute('SELECT * FROM classes').fetchall()
    return jsonify([dict(c) for c in classes])

@app.route('/api/students')
def get_students():
    city_id = request.args.get('city_id', type=int)
    conn = app.config.get('DB_CONN')
    if not conn:
        init_db()
        conn = app.config['DB_CONN']
    if city_id:
        students = conn.execute('SELECT * FROM students WHERE city_id = ?', (city_id,)).fetchall()
    else:
        students = conn.execute('SELECT * FROM students').fetchall()
    return jsonify([dict(s) for s in students])

# Initialize database when the app starts
with app.app_context():
    init_db()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

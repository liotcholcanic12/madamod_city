from flask import Flask, jsonify, render_template, request
import sqlite3
import os

app = Flask(__name__)

DATABASE = 'data.db'

def init_db():
    conn = sqlite3.connect(DATABASE)
    conn.execute('CREATE TABLE IF NOT EXISTS cities (id INTEGER PRIMARY KEY, name TEXT)')
    conn.execute('CREATE TABLE IF NOT EXISTS classes (id INTEGER PRIMARY KEY, city_id INTEGER, name TEXT)')
    conn.execute('CREATE TABLE IF NOT EXISTS students (id INTEGER PRIMARY KEY, name TEXT, city_id INTEGER, class_id INTEGER, total_points INTEGER)')
    
    # Insert sample data
    conn.execute("INSERT OR IGNORE INTO cities VALUES (1, 'Madamod'), (2, 'المنشاة')")
    conn.execute("INSERT OR IGNORE INTO classes VALUES (1, 1, 'Mathematics 101'), (2, 1, 'Physics 202'), (3, 2, 'الرياضيات')")
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/cities')
def get_cities():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cities = conn.execute('SELECT * FROM cities').fetchall()
    conn.close()
    return jsonify([dict(c) for c in cities])

@app.route('/api/classes')
def get_classes():
    city_id = request.args.get('city_id', type=int)
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    if city_id:
        classes = conn.execute('SELECT * FROM classes WHERE city_id = ?', (city_id,)).fetchall()
    else:
        classes = conn.execute('SELECT * FROM classes').fetchall()
    conn.close()
    return jsonify([dict(c) for c in classes])

@app.route('/api/students')
def get_students():
    city_id = request.args.get('city_id', type=int)
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    if city_id:
        students = conn.execute('SELECT * FROM students WHERE city_id = ?', (city_id,)).fetchall()
    else:
        students = conn.execute('SELECT * FROM students').fetchall()
    conn.close()
    return jsonify([dict(s) for s in students])

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

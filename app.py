from flask import Flask, render_template, request, jsonify, send_file
import os
from datetime import datetime
import sqlite3
import json

app = Flask(__name__)

# TEMPORARY: Using SQLite instead of Supabase for Vercel testing
DATABASE = 'test.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.execute('CREATE TABLE IF NOT EXISTS cities (id INTEGER PRIMARY KEY, name TEXT)')
        conn.execute('CREATE TABLE IF NOT EXISTS classes (id INTEGER PRIMARY KEY, city_id INTEGER, name TEXT)')
        conn.execute('CREATE TABLE IF NOT EXISTS students (id INTEGER PRIMARY KEY, name TEXT, city_id INTEGER, class_id INTEGER, total_points INTEGER)')
        
        # Insert sample data
        conn.execute("INSERT OR IGNORE INTO cities VALUES (1, 'Madamod'), (2, 'المنشاة')")
        conn.execute("INSERT OR IGNORE INTO classes VALUES (1, 1, 'Mathematics'), (2, 1, 'Physics'), (3, 2, 'الرياضيات')")
        conn.execute("INSERT OR IGNORE INTO students VALUES (1, 'Test', 1, 1, 50)")

init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/cities')
def get_cities():
    db = get_db()
    cities = db.execute('SELECT * FROM cities').fetchall()
    return jsonify([dict(c) for c in cities])

@app.route('/api/classes')
def get_classes():
    city_id = request.args.get('city_id', type=int)
    db = get_db()
    if city_id:
        classes = db.execute('SELECT * FROM classes WHERE city_id = ?', (city_id,)).fetchall()
    else:
        classes = db.execute('SELECT * FROM classes').fetchall()
    return jsonify([dict(c) for c in classes])

@app.route('/api/students')
def get_students():
    city_id = request.args.get('city_id', type=int)
    db = get_db()
    if city_id:
        students = db.execute('SELECT * FROM students WHERE city_id = ?', (city_id,)).fetchall()
    else:
        students = db.execute('SELECT * FROM students').fetchall()
    return jsonify([dict(s) for s in students])

@app.route('/api/students', methods=['POST'])
def add_student():
    data = request.json
    db = get_db()
    db.execute('INSERT INTO students (name, city_id, class_id, total_points) VALUES (?, ?, ?, 0)',
               (data['name'], data['city_id'], data.get('class_id')))
    db.commit()
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

from flask import Flask, jsonify, render_template, request
import sqlite3

app = Flask(__name__)

DATABASE = 'data.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.execute('CREATE TABLE IF NOT EXISTS cities (id INTEGER PRIMARY KEY, name TEXT)')
        conn.execute('CREATE TABLE IF NOT EXISTS classes (id INTEGER PRIMARY KEY, city_id INTEGER, name TEXT)')
        conn.execute('INSERT OR IGNORE INTO cities VALUES (1, "Madamod"), (2, "المنشاة")')
        conn.execute('INSERT OR IGNORE INTO classes VALUES (1, 1, "Mathematics 101"), (2, 1, "Physics 202"), (3, 2, "الرياضيات")')
        conn.commit()

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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

from flask import Flask, jsonify, render_template, request
import os
import sqlite3
from datetime import datetime

app = Flask(__name__)

# Simple in-memory storage for testing
DATA = {
    'cities': [{'id': 1, 'name': 'Madamod'}, {'id': 2, 'name': 'المنشاة'}],
    'classes': [
        {'id': 1, 'city_id': 1, 'name': 'Mathematics 101'},
        {'id': 2, 'city_id': 1, 'name': 'Physics 202'},
        {'id': 3, 'city_id': 2, 'name': 'الرياضيات'}
    ],
    'students': [
        {'id': 1, 'name': 'Test Student 1', 'city_id': 1, 'class_id': 1, 'total_points': 50},
        {'id': 2, 'name': 'Test Student 2', 'city_id': 2, 'class_id': 3, 'total_points': 75}
    ]
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/cities')
def get_cities():
    return jsonify(DATA['cities'])

@app.route('/api/classes')
def get_classes():
    city_id = request.args.get('city_id', type=int)
    if city_id:
        return jsonify([c for c in DATA['classes'] if c['city_id'] == city_id])
    return jsonify(DATA['classes'])

@app.route('/api/students')
def get_students():
    city_id = request.args.get('city_id', type=int)
    students = DATA['students']
    if city_id:
        students = [s for s in students if s['city_id'] == city_id]
    return jsonify(students)

@app.route('/api/students', methods=['POST'])
def add_student():
    data = request.json
    new_id = max([s['id'] for s in DATA['students']]) + 1 if DATA['students'] else 1
    DATA['students'].append({
        'id': new_id,
        'name': data['name'],
        'city_id': data['city_id'],
        'class_id': data.get('class_id'),
        'total_points': 0
    })
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

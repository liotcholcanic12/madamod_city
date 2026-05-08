from flask import Flask, render_template, request, jsonify, send_file
import sqlite3
import os
import io
from datetime import datetime
import json

app = Flask(__name__)

# Use a persistent file path that Vercel allows (temporary directory)
DATABASE = '/tmp/school_tasks.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    
    # Create tables
    conn.execute('''CREATE TABLE IF NOT EXISTS cities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    conn.execute('''CREATE TABLE IF NOT EXISTS classes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        city_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (city_id) REFERENCES cities (id),
        UNIQUE(city_id, name)
    )''')
    
    conn.execute('''CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        city_id INTEGER NOT NULL,
        class_id INTEGER,
        total_points INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (city_id) REFERENCES cities (id),
        FOREIGN KEY (class_id) REFERENCES classes (id),
        UNIQUE(name, city_id)
    )''')
    
    conn.execute('''CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        class_id INTEGER NOT NULL,
        task_name TEXT NOT NULL,
        max_points INTEGER DEFAULT 100,
        FOREIGN KEY (class_id) REFERENCES classes (id) ON DELETE CASCADE,
        UNIQUE(class_id, task_name)
    )''')
    
    conn.execute('''CREATE TABLE IF NOT EXISTS approvals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        class_id INTEGER NOT NULL,
        task_id INTEGER NOT NULL,
        grade_points INTEGER NOT NULL,
        mentor_signature TEXT NOT NULL,
        approval_date DATE NOT NULL,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (student_id) REFERENCES students (id),
        FOREIGN KEY (class_id) REFERENCES classes (id),
        FOREIGN KEY (task_id) REFERENCES tasks (id)
    )''')
    
    conn.execute('''CREATE TABLE IF NOT EXISTS activity_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        action_type TEXT NOT NULL,
        description TEXT NOT NULL,
        user_name TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Insert sample data if empty
    cursor = conn.execute('SELECT COUNT(*) as count FROM cities')
    if cursor.fetchone()['count'] == 0:
        # Insert cities
        conn.execute("INSERT INTO cities (name) VALUES ('Madamod'), ('المنشاة')")
        
        # Insert classes
        conn.execute("INSERT INTO classes (city_id, name) SELECT id, 'Mathematics 101' FROM cities WHERE name = 'Madamod'")
        conn.execute("INSERT INTO classes (city_id, name) SELECT id, 'Physics 202' FROM cities WHERE name = 'Madamod'")
        conn.execute("INSERT INTO classes (city_id, name) SELECT id, 'Literature 105' FROM cities WHERE name = 'Madamod'")
        conn.execute("INSERT INTO classes (city_id, name) SELECT id, 'الرياضيات' FROM cities WHERE name = 'المنشاة'")
        conn.execute("INSERT INTO classes (city_id, name) SELECT id, 'العلوم' FROM cities WHERE name = 'المنشاة'")
        conn.execute("INSERT INTO classes (city_id, name) SELECT id, 'اللغة العربية' FROM cities WHERE name = 'المنشاة'")
        
        # Insert tasks
        conn.execute("INSERT INTO tasks (class_id, task_name, max_points) SELECT id, 'Algebra Worksheet', 50 FROM classes WHERE name = 'Mathematics 101'")
        conn.execute("INSERT INTO tasks (class_id, task_name, max_points) SELECT id, 'Calculus Problems', 100 FROM classes WHERE name = 'Mathematics 101'")
        conn.execute("INSERT INTO tasks (class_id, task_name, max_points) SELECT id, 'Newton''s Laws Lab', 100 FROM classes WHERE name = 'Physics 202'")
        conn.execute("INSERT INTO tasks (class_id, task_name, max_points) SELECT id, 'Shakespeare Essay', 100 FROM classes WHERE name = 'Literature 105'")
        conn.execute("INSERT INTO tasks (class_id, task_name, max_points) SELECT id, 'ورقة عمل', 50 FROM classes WHERE name = 'الرياضيات'")
        conn.execute("INSERT INTO tasks (class_id, task_name, max_points) SELECT id, 'تجربة علمية', 100 FROM classes WHERE name = 'العلوم'")
    
    conn.commit()
    conn.close()

# Initialize database
init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/cities')
def get_cities():
    db = get_db()
    cities = db.execute('SELECT * FROM cities ORDER BY name').fetchall()
    db.close()
    return jsonify([dict(c) for c in cities])

@app.route('/api/classes')
def get_classes():
    city_id = request.args.get('city_id', type=int)
    db = get_db()
    if city_id:
        classes = db.execute('SELECT * FROM classes WHERE city_id = ? ORDER BY name', (city_id,)).fetchall()
    else:
        classes = db.execute('SELECT * FROM classes ORDER BY name').fetchall()
    db.close()
    return jsonify([dict(c) for c in classes])

@app.route('/api/tasks/<int:class_id>')
def get_tasks(class_id):
    db = get_db()
    tasks = db.execute('SELECT * FROM tasks WHERE class_id = ? ORDER BY task_name', (class_id,)).fetchall()
    db.close()
    return jsonify([dict(t) for t in tasks])

@app.route('/api/students')
def get_students():
    city_id = request.args.get('city_id', type=int)
    class_id = request.args.get('class_id', type=int)  # Add this line
    
    db = get_db()
    
    query = '''
        SELECT 
            s.*,
            c.name as city_name,
            cl.name as class_name,
            (SELECT COUNT(*) FROM approvals a WHERE a.student_id = s.id) as tasks_completed,
            (SELECT COUNT(*) FROM tasks t WHERE t.class_id = s.class_id) as total_tasks
        FROM students s
        JOIN cities c ON s.city_id = c.id
        LEFT JOIN classes cl ON s.class_id = cl.id
        WHERE 1=1
    '''
    params = []
    
    if city_id:
        query += ' AND s.city_id = ?'
        params.append(city_id)
    
    if class_id:  # Add this block
        query += ' AND s.class_id = ?'
        params.append(class_id)
    
    query += ' ORDER BY s.total_points DESC'
    
    students = db.execute(query, params).fetchall()
    db.close()
    return jsonify([dict(s) for s in students])

@app.route('/api/students', methods=['POST'])
def add_student():
    try:
        data = request.json
        db = get_db()
        db.execute(
            'INSERT INTO students (name, city_id, class_id, total_points) VALUES (?, ?, ?, 0)',
            (data['name'], data['city_id'], data.get('class_id'))
        )
        db.commit()
        db.close()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/approvals', methods=['POST'])
def add_approval():
    try:
        data = request.json
        db = get_db()
        
        # Check if student exists
        student = db.execute(
            'SELECT id, total_points FROM students WHERE name = ? AND city_id = ?',
            (data['student_name'], data['city_id'])
        ).fetchone()
        
        if not student:
            # Create new student
            cursor = db.execute(
                'INSERT INTO students (name, city_id, class_id, total_points) VALUES (?, ?, ?, 0)',
                (data['student_name'], data['city_id'], data['class_id'])
            )
            student_id = cursor.lastrowid
            current_total = 0
        else:
            student_id = student['id']
            current_total = student['total_points']
        
        # Add approval
        db.execute(
            '''INSERT INTO approvals (student_id, class_id, task_id, grade_points, mentor_signature, approval_date)
               VALUES (?, ?, ?, ?, ?, ?)''',
            (student_id, data['class_id'], data['task_id'], data['grade_points'], 
             data['mentor_signature'], data['approval_date'])
        )
        
        # Update total points
        new_total = current_total + data['grade_points']
        db.execute('UPDATE students SET total_points = ? WHERE id = ?', (new_total, student_id))
        
        # Log activity
        db.execute(
            'INSERT INTO activity_log (action_type, description, user_name) VALUES (?, ?, ?)',
            ('ADD_APPROVAL', f"Added {data['grade_points']} points for {data['student_name']}", data['mentor_signature'])
        )
        
        db.commit()
        db.close()
        return jsonify({'success': True, 'student_total': new_total})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/students/<int:student_id>')
def get_student_details(student_id):
    db = get_db()
    student = db.execute(
        'SELECT s.*, c.name as city_name, cl.name as class_name FROM students s JOIN cities c ON s.city_id = c.id LEFT JOIN classes cl ON s.class_id = cl.id WHERE s.id = ?',
        (student_id,)
    ).fetchone()
    
    approvals = db.execute(
        'SELECT a.*, t.task_name, t.max_points FROM approvals a JOIN tasks t ON a.task_id = t.id WHERE a.student_id = ? ORDER BY a.approval_date DESC',
        (student_id,)
    ).fetchall()
    db.close()
    
    return jsonify({
        'student': dict(student) if student else None,
        'approvals': [dict(a) for a in approvals]
    })

@app.route('/api/activity-log')
def get_activity_log():
    db = get_db()
    logs = db.execute('SELECT * FROM activity_log ORDER BY timestamp DESC LIMIT 50').fetchall()
    db.close()
    return jsonify([dict(l) for l in logs])

@app.route('/api/classes', methods=['POST'])
def add_class():
    try:
        data = request.json
        db = get_db()
        db.execute('INSERT INTO classes (city_id, name) VALUES (?, ?)', (data['city_id'], data['name']))
        db.commit()
        db.close()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/tasks', methods=['POST'])
def add_task():
    try:
        data = request.json
        db = get_db()
        db.execute('INSERT INTO tasks (class_id, task_name, max_points) VALUES (?, ?, ?)',
                   (data['class_id'], data['task_name'], data.get('max_points', 100)))
        db.commit()
        db.close()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/approvals/<int:approval_id>', methods=['DELETE'])
def delete_approval(approval_id):
    try:
        db = get_db()
        approval = db.execute('SELECT student_id, grade_points FROM approvals WHERE id = ?', (approval_id,)).fetchone()
        if approval:
            db.execute('DELETE FROM approvals WHERE id = ?', (approval_id,))
            db.execute('UPDATE students SET total_points = total_points - ? WHERE id = ?', (approval['grade_points'], approval['student_id']))
            db.commit()
        db.close()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/download-excel')
def download_excel():
    try:
        import openpyxl
        from openpyxl.styles import Font, PatternFill
        
        city_id = request.args.get('city_id', type=int)
        db = get_db()
        
        query = '''
            SELECT s.name, c.name as city_name, cl.name as class_name, s.total_points
            FROM students s
            JOIN cities c ON s.city_id = c.id
            LEFT JOIN classes cl ON s.class_id = cl.id
        '''
        params = []
        if city_id:
            query += ' WHERE s.city_id = ?'
            params.append(city_id)
        query += ' ORDER BY s.total_points DESC'
        
        students = db.execute(query, params).fetchall()
        db.close()
        
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Students"
        
        headers = ['Student Name', 'City', 'Class', 'Total Points']
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill(start_color="0D6EFD", end_color="0D6EFD", fill_type="solid")
        
        for row, student in enumerate(students, 2):
            ws.cell(row=row, column=1, value=student['name'])
            ws.cell(row=row, column=2, value=student['city_name'])
            ws.cell(row=row, column=3, value=student['class_name'] or 'Not Assigned')
            ws.cell(row=row, column=4, value=student['total_points'])
        
        excel_file = io.BytesIO()
        wb.save(excel_file)
        excel_file.seek(0)
        
        return send_file(excel_file, as_attachment=True, download_name=f'students_{datetime.now().strftime("%Y%m%d")}.xlsx', mimetype='application/vnd.openpyxl')
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

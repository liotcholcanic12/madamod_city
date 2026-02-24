import os
import sqlite3
import io
from datetime import datetime
from flask import Flask, render_template, request, jsonify, g, send_file
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-key-change-in-production'
DATABASE = 'school_tasks.db'

# Database helper functions
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()
        
        # Add sample data if empty
        cur = db.execute("SELECT COUNT(*) as count FROM classes")
        if cur.fetchone()['count'] == 0:
            # Sample classes - MODIFY THESE TO CHANGE CLASS NAMES
            classes = [
                ('al7an',),
                ('ejbya',),
                ('2odas',)
            ]
            db.executemany("INSERT INTO classes (name) VALUES (?)", classes)
            
            # Sample tasks for each class - MODIFY THESE TO CHANGE TASKS
            tasks = [
                (1, 'kanon al eyman', 50)
            ]
            db.executemany(
                "INSERT INTO tasks (class_id, task_name, max_points) VALUES (?, ?, ?)",
                tasks
            )
            db.commit()

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/classes')
def get_classes():
    db = get_db()
    classes = db.execute("SELECT * FROM classes ORDER BY name").fetchall()
    return jsonify([dict(c) for c in classes])

@app.route('/api/tasks/<int:class_id>')
def get_tasks(class_id):
    db = get_db()
    tasks = db.execute(
        "SELECT * FROM tasks WHERE class_id = ? ORDER BY task_name",
        (class_id,)
    ).fetchall()
    return jsonify([dict(t) for t in tasks])

@app.route('/api/approvals')
def get_approvals():
    db = get_db()
    class_id = request.args.get('class_id', type=int)
    
    query = """
        SELECT a.*, c.name as class_name, t.task_name, t.max_points
        FROM approvals a
        JOIN classes c ON a.class_id = c.id
        JOIN tasks t ON a.task_id = t.id
    """
    params = []
    if class_id:
        query += " WHERE a.class_id = ?"
        params.append(class_id)
    query += " ORDER BY a.approval_date DESC, a.student_name"
    
    approvals = db.execute(query, params).fetchall()
    return jsonify([dict(a) for a in approvals])

@app.route('/api/approvals', methods=['POST'])
def add_approval():
    data = request.json
    db = get_db()
    
    try:
        cursor = db.execute("""
            INSERT INTO approvals 
            (student_name, class_id, task_id, grade_points, mentor_signature, approval_date, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            data['student_name'],
            data['class_id'],
            data['task_id'],
            data['grade_points'],
            data['mentor_signature'],
            data['approval_date'],
            data.get('notes', '')
        ))
        
        # Add to activity log
        db.execute("""
            INSERT INTO activity_log (action_type, description, user_name)
            VALUES (?, ?, ?)
        """, (
            'ADD_APPROVAL',
            f"Added {data['grade_points']} points for {data['student_name']}",
            data['mentor_signature']
        ))
        
        db.commit()
        return jsonify({'id': cursor.lastrowid, 'message': 'Approval added successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/approvals/<int:approval_id>', methods=['PUT'])
def update_approval(approval_id):
    data = request.json
    db = get_db()
    
    try:
        # Get old data for activity log
        old = db.execute("SELECT * FROM approvals WHERE id = ?", (approval_id,)).fetchone()
        
        db.execute("""
            UPDATE approvals 
            SET student_name = ?, grade_points = ?, mentor_signature = ?, 
                approval_date = ?, notes = ?
            WHERE id = ?
        """, (
            data['student_name'],
            data['grade_points'],
            data['mentor_signature'],
            data['approval_date'],
            data.get('notes', ''),
            approval_id
        ))
        
        # Add to activity log
        db.execute("""
            INSERT INTO activity_log (action_type, description, user_name)
            VALUES (?, ?, ?)
        """, (
            'UPDATE_APPROVAL',
            f"Updated points for {data['student_name']} from {old['grade_points']} to {data['grade_points']}",
            data['mentor_signature']
        ))
        
        db.commit()
        return jsonify({'message': 'Approval updated successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/approvals/<int:approval_id>', methods=['DELETE'])
def delete_approval(approval_id):
    db = get_db()
    
    # Get data for activity log
    approval = db.execute("SELECT * FROM approvals WHERE id = ?", (approval_id,)).fetchone()
    
    db.execute("DELETE FROM approvals WHERE id = ?", (approval_id,))
    
    # Add to activity log
    db.execute("""
        INSERT INTO activity_log (action_type, description, user_name)
        VALUES (?, ?, ?)
    """, (
        'DELETE_APPROVAL',
        f"Deleted approval for {approval['student_name']}",
        'System'
    ))
    
    db.commit()
    return jsonify({'message': 'Approval deleted'})

@app.route('/api/classes', methods=['POST'])
def add_class():
    data = request.json
    db = get_db()
    
    try:
        cursor = db.execute(
            "INSERT INTO classes (name) VALUES (?)",
            (data['name'],)
        )
        
        # Add to activity log
        db.execute("""
            INSERT INTO activity_log (action_type, description, user_name)
            VALUES (?, ?, ?)
        """, (
            'ADD_CLASS',
            f"Added new class: {data['name']}",
            'Admin'
        ))
        
        db.commit()
        return jsonify({'id': cursor.lastrowid, 'message': 'Class added successfully'})
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Class already exists'}), 400

@app.route('/api/tasks', methods=['POST'])
def add_task():
    data = request.json
    db = get_db()
    
    try:
        cursor = db.execute("""
            INSERT INTO tasks (class_id, task_name, max_points) 
            VALUES (?, ?, ?)
        """, (data['class_id'], data['task_name'], data.get('max_points', 100)))
        
        # Add to activity log
        db.execute("""
            INSERT INTO activity_log (action_type, description, user_name)
            VALUES (?, ?, ?)
        """, (
            'ADD_TASK',
            f"Added new task: {data['task_name']} (Max: {data.get('max_points', 100)} points)",
            'Admin'
        ))
        
        db.commit()
        return jsonify({'id': cursor.lastrowid, 'message': 'Task added successfully'})
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Task already exists for this class'}), 400

@app.route('/api/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    db = get_db()
    
    task = db.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    db.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    
    # Add to activity log
    db.execute("""
        INSERT INTO activity_log (action_type, description, user_name)
        VALUES (?, ?, ?)
    """, (
        'DELETE_TASK',
        f"Deleted task: {task['task_name']}",
        'Admin'
    ))
    
    db.commit()
    return jsonify({'message': 'Task deleted'})

@app.route('/api/activity-log')
def get_activity_log():
    db = get_db()
    
    activities = db.execute("""
        SELECT * FROM activity_log 
        ORDER BY timestamp DESC 
        LIMIT 20
    """).fetchall()
    
    return jsonify([dict(a) for a in activities])

@app.route('/api/download-excel')
def download_excel():
    db = get_db()
    
    # Get all approvals with details
    approvals = db.execute("""
        SELECT 
            a.approval_date,
            a.student_name,
            c.name as class_name,
            t.task_name,
            a.grade_points,
            t.max_points,
            a.mentor_signature,
            a.notes
        FROM approvals a
        JOIN classes c ON a.class_id = c.id
        JOIN tasks t ON a.task_id = t.id
        ORDER BY a.approval_date DESC, a.student_name
    """).fetchall()
    
    # Create Excel file
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Task Approvals"
    
    # Headers
    headers = ['Date', 'Student', 'Class', 'Task', 'Points', 'Max Points', 'Mentor', 'Notes']
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill(start_color="0D6EFD", end_color="0D6EFD", fill_type="solid")
        cell.alignment = Alignment(horizontal="center")
    
    # Data
    for row, approval in enumerate(approvals, 2):
        for col, value in enumerate(approval, 1):
            cell = ws.cell(row=row, column=col, value=value)
            if col == 5:  # Points column
                max_points = approval[5]
                if value == max_points:
                    cell.font = Font(color="008000")  # Green for full points
                elif value >= max_points * 0.7:
                    cell.font = Font(color="FFA500")  # Orange for partial
    
    # Auto-adjust column widths
    for col in range(1, len(headers) + 1):
        ws.column_dimensions[openpyxl.utils.get_column_letter(col)].width = 15
    
    # Add summary sheet
    ws_summary = wb.create_sheet("Summary")
    ws_summary.append(['Class', 'Total Students', 'Avg Points', 'Total Tasks'])
    
    # Get summary data
    summary = db.execute("""
        SELECT 
            c.name,
            COUNT(DISTINCT a.student_name) as student_count,
            AVG(a.grade_points) as avg_points,
            COUNT(a.id) as task_count
        FROM classes c
        LEFT JOIN approvals a ON c.id = a.class_id
        GROUP BY c.id
    """).fetchall()
    
    for row in summary:
        ws_summary.append([row[0], row[1], round(row[2] or 0, 1), row[3]])
    
    # Save to bytes buffer
    excel_file = io.BytesIO()
    wb.save(excel_file)
    excel_file.seek(0)
    
    # Generate filename with date
    filename = f"task_approvals_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    
    return send_file(
        excel_file,
        as_attachment=True,
        download_name=filename,
        mimetype='application/vnd.openpyxl'
    )

# Initialize database on startup
with app.app_context():
    init_db()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

app = app 
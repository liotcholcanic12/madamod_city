import os
import requests
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file
from dotenv import load_dotenv
import io
import openpyxl
from openpyxl.styles import Font, PatternFill

load_dotenv()
app = Flask(__name__)

SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')

def sb(table):
    """Base URL for a Supabase table."""
    return f"{SUPABASE_URL}/rest/v1/{table}"

def headers(extra=None):
    h = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }
    if extra:
        h.update(extra)
    return h

def get(table, params=None):
    r = requests.get(sb(table), headers=headers(), params=params)
    return r.json()

def post(table, data):
    r = requests.post(sb(table), headers=headers(), json=data)
    return r.json()

def patch(table, match_params, data):
    r = requests.patch(sb(table), headers=headers(), params=match_params, json=data)
    return r.json()

def delete(table, match_params):
    r = requests.delete(sb(table), headers=headers(), params=match_params)
    return r.status_code

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/cities')
def get_cities():
    try:
        data = get('cities', {'order': 'name'})
        return jsonify(data)
    except Exception as e:
        print(f"[get_cities] Error: {e}")
        return jsonify([])

@app.route('/api/classes')
def get_classes():
    try:
        params = {'order': 'name'}
        city_id = request.args.get('city_id')
        if city_id:
            params['city_id'] = f'eq.{city_id}'
        data = get('classes', params)
        return jsonify(data)
    except Exception as e:
        print(f"[get_classes] Error: {e}")
        return jsonify([])

@app.route('/api/classes', methods=['POST'])
def add_class():
    try:
        data = request.json
        post('classes', {'city_id': data['city_id'], 'name': data['name']})
        _log('ADD_CLASS', f"Added class: {data['name']}", 'Admin')
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/tasks/<int:class_id>')
def get_tasks(class_id):
    try:
        data = get('tasks', {'class_id': f'eq.{class_id}', 'order': 'task_name'})
        return jsonify(data)
    except Exception as e:
        return jsonify([])

@app.route('/api/tasks', methods=['POST'])
def add_task():
    try:
        data = request.json
        post('tasks', {
            'class_id': data['class_id'],
            'task_name': data['task_name'],
            'max_points': data.get('max_points', 100)
        })
        _log('ADD_TASK', f"Added task: {data['task_name']}", 'Admin')
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/students')
def get_students():
    try:
        city_id = request.args.get('city_id')
        class_id = request.args.get('class_id')

        params = {'order': 'total_points.desc'}
        if city_id:
            params['city_id'] = f'eq.{city_id}'
        if class_id:
            params['class_id'] = f'eq.{class_id}'
        params['select'] = '*,cities(name),classes(name)'

        students = get('students', params)

        # Get all approvals and tasks in 2 bulk calls
        student_ids = [s['id'] for s in students]
        class_ids = list({s['class_id'] for s in students if s.get('class_id')})

        approvals_count = {}
        if student_ids:
            approvals = get('approvals', {
                'student_id': f'in.({",".join(str(i) for i in student_ids)})',
                'select': 'student_id'
            })
            for a in approvals:
                sid = a['student_id']
                approvals_count[sid] = approvals_count.get(sid, 0) + 1

        tasks_count = {}
        if class_ids:
            tasks = get('tasks', {
                'class_id': f'in.({",".join(str(i) for i in class_ids)})',
                'select': 'class_id'
            })
            for t in tasks:
                cid = t['class_id']
                tasks_count[cid] = tasks_count.get(cid, 0) + 1

        result = []
        for s in students:
            result.append({
                'id': s['id'],
                'name': s['name'],
                'city_name': s.get('cities', {}).get('name', 'Unknown') if s.get('cities') else 'Unknown',
                'class_name': s.get('classes', {}).get('name', 'Not Assigned') if s.get('classes') else 'Not Assigned',
                'total_points': s['total_points'],
                'tasks_completed': approvals_count.get(s['id'], 0),
                'total_tasks': tasks_count.get(s.get('class_id'), 0),
                'created_at': s['created_at']
            })

        return jsonify(result)
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify([])

@app.route('/api/students', methods=['POST'])
def add_student():
    try:
        data = request.json
        post('students', {
            'name': data['name'],
            'city_id': data['city_id'],
            'class_id': data.get('class_id'),
            'total_points': 0
        })
        _log('ADD_STUDENT', f"Added student: {data['name']}", 'Admin')
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/students/<int:student_id>')
def get_student_details(student_id):
    try:
        students = get('students', {
            'id': f'eq.{student_id}',
            'select': '*,cities(name),classes(name)'
        })
        if not students:
            return jsonify({'student': None, 'approvals': []})

        s = students[0]
        student_data = {
            **s,
            'city_name': s.get('cities', {}).get('name', 'Unknown') if s.get('cities') else 'Unknown',
            'class_name': s.get('classes', {}).get('name', 'Not Assigned') if s.get('classes') else 'Not Assigned',
        }

        approvals = get('approvals', {
            'student_id': f'eq.{student_id}',
            'select': '*,tasks(task_name,max_points)',
            'order': 'approval_date.desc'
        })

        return jsonify({'student': student_data, 'approvals': approvals})
    except Exception as e:
        return jsonify({'student': None, 'approvals': []})

@app.route('/api/approvals', methods=['POST'])
def add_approval():
    try:
        data = request.json

        # Find or create student
        existing = get('students', {
            'name': f'eq.{data["student_name"]}',
            'city_id': f'eq.{data["city_id"]}'
        })

        if not existing:
            new_student = post('students', {
                'name': data['student_name'],
                'city_id': data['city_id'],
                'class_id': data['class_id'],
                'total_points': 0
            })
            student_id = new_student[0]['id']
            current_total = 0
        else:
            student_id = existing[0]['id']
            current_total = existing[0]['total_points']

        # Add approval
        post('approvals', {
            'student_id': student_id,
            'class_id': data['class_id'],
            'task_id': data['task_id'],
            'grade_points': data['grade_points'],
            'mentor_signature': data['mentor_signature'],
            'approval_date': data['approval_date']
        })

        # Update total points
        new_total = current_total + data['grade_points']
        patch('students', {'id': f'eq.{student_id}'}, {'total_points': new_total})

        _log('ADD_APPROVAL',
             f"Added {data['grade_points']} pts for {data['student_name']} (Total: {new_total})",
             data['mentor_signature'])

        return jsonify({'success': True, 'student_total': new_total})
    except Exception as e:
        print(f"[add_approval] Error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/approvals/<int:approval_id>', methods=['DELETE'])
def delete_approval(approval_id):
    try:
        approval = get('approvals', {'id': f'eq.{approval_id}', 'select': 'student_id,grade_points'})
        if approval:
            student_id = approval[0]['student_id']
            points = approval[0]['grade_points']
            delete('approvals', {'id': f'eq.{approval_id}'})
            student = get('students', {'id': f'eq.{student_id}', 'select': 'total_points'})
            if student:
                new_total = max(0, student[0]['total_points'] - points)
                patch('students', {'id': f'eq.{student_id}'}, {'total_points': new_total})
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/activity-log')
def get_activity_log():
    try:
        data = get('activity_log', {'order': 'timestamp.desc', 'limit': '50'})
        return jsonify(data)
    except Exception as e:
        return jsonify([])

@app.route('/api/debug-students')
def debug_students():
    try:
        data = get('students', {'select': '*', 'limit': '5'})
        return jsonify({'success': True, 'count': len(data), 'data': data})
    except Exception as e:
        import traceback
        return jsonify({'success': False, 'error': str(e), 'trace': traceback.format_exc()})

@app.route('/api/download-excel')
def download_excel():
    try:
        city_id = request.args.get('city_id')
        params = {'select': '*,cities(name),classes(name)', 'order': 'total_points.desc'}
        if city_id:
            params['city_id'] = f'eq.{city_id}'
        students = get('students', params)

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Students"
        headers_row = ['Student Name', 'City', 'Class', 'Total Points']
        for col, h in enumerate(headers_row, 1):
            cell = ws.cell(row=1, column=col, value=h)
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill(start_color="0D6EFD", end_color="0D6EFD", fill_type="solid")

        for row, s in enumerate(students, 2):
            ws.cell(row=row, column=1, value=s['name'])
            ws.cell(row=row, column=2, value=s.get('cities', {}).get('name', '') if s.get('cities') else '')
            ws.cell(row=row, column=3, value=s.get('classes', {}).get('name', '') if s.get('classes') else '')
            ws.cell(row=row, column=4, value=s['total_points'])

        f = io.BytesIO()
        wb.save(f)
        f.seek(0)
        return send_file(f, as_attachment=True,
                        download_name=f'students_{datetime.now().strftime("%Y%m%d")}.xlsx',
                        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def _log(action_type, description, user_name):
    try:
        post('activity_log', {
            'action_type': action_type,
            'description': description,
            'user_name': user_name
        })
    except Exception as e:
        print(f"[_log] Warning: {e}")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

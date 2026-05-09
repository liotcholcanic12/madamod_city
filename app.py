import os
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file
from supabase import create_client, Client
from dotenv import load_dotenv
import io
import openpyxl
from openpyxl.styles import Font, PatternFill

load_dotenv()

app = Flask(__name__)

# Initialize Supabase
supabase: Client = create_client(
    os.environ.get('SUPABASE_URL'),
    os.environ.get('SUPABASE_KEY')
)


@app.route('/')
def index():
    return render_template('index.html')


# ── Cities ──────────────────────────────────────────────────────────────────

@app.route('/api/cities')
def get_cities():
    try:
        result = supabase.table('cities').select('*').order('name').execute()
        return jsonify(result.data)
    except Exception as e:
        print(f"[get_cities] Error: {e}")
        return jsonify([])


@app.route('/api/debug-students')
def debug_students():
    try:
        result = supabase.table('students').select('*').execute()
        return jsonify({'success': True, 'count': len(result.data), 'data': result.data})
    except Exception as e:
        import traceback
        return jsonify({'success': False, 'error': str(e), 'trace': traceback.format_exc()})

# ── Classes ─────────────────────────────────────────────────────────────────

@app.route('/api/classes')
def get_classes():
    try:
        city_id = request.args.get('city_id', type=int)
        query = supabase.table('classes').select('*')
        if city_id:
            query = query.eq('city_id', city_id)
        result = query.order('name').execute()
        return jsonify(result.data)
    except Exception as e:
        print(f"[get_classes] Error: {e}")
        return jsonify([])


@app.route('/api/classes', methods=['POST'])
def add_class():
    try:
        data = request.json
        supabase.table('classes').insert({
            'city_id': data['city_id'],
            'name': data['name']
        }).execute()
        _log('ADD_CLASS', f"Added new class: {data['name']}", 'Admin')
        return jsonify({'success': True})
    except Exception as e:
        print(f"[add_class] Error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 400


# ── Tasks ────────────────────────────────────────────────────────────────────

@app.route('/api/tasks/<int:class_id>')
def get_tasks(class_id):
    try:
        result = supabase.table('tasks').select('*').eq('class_id', class_id).order('task_name').execute()
        return jsonify(result.data)
    except Exception as e:
        print(f"[get_tasks] Error: {e}")
        return jsonify([])


@app.route('/api/tasks', methods=['POST'])
def add_task():
    try:
        data = request.json
        supabase.table('tasks').insert({
            'class_id': data['class_id'],
            'task_name': data['task_name'],
            'max_points': data.get('max_points', 100)
        }).execute()
        _log('ADD_TASK', f"Added new task: {data['task_name']}", 'Admin')
        return jsonify({'success': True})
    except Exception as e:
        print(f"[add_task] Error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 400


# ── Students ─────────────────────────────────────────────────────────────────

@app.route('/api/students')
def get_students():
    """
    FIX: The original version made 3 extra DB calls per student (class name,
    approvals count, tasks count) — an N+1 problem. This version fetches
    everything in 4 queries total regardless of how many students there are.
    """
    try:
        city_id = request.args.get('city_id', type=int)
        class_id = request.args.get('class_id', type=int)

        # 1) Fetch students with their city and class in one query
        query = supabase.table('students').select('*, cities(name), classes(name)')
        if city_id:
            query = query.eq('city_id', city_id)
        if class_id:
            query = query.eq('class_id', class_id)
        students_result = query.execute()

        if not students_result.data:
            return jsonify([])

        student_ids = [s['id'] for s in students_result.data]
        class_ids   = list({s['class_id'] for s in students_result.data if s.get('class_id')})

        # 2) Fetch all approvals for these students in one query
        approvals_result = supabase.table('approvals').select('student_id').in_('student_id', student_ids).execute()
        approvals_count = {}
        for a in approvals_result.data:
            approvals_count[a['student_id']] = approvals_count.get(a['student_id'], 0) + 1

        # 3) Fetch task counts per class in one query
        tasks_result = supabase.table('tasks').select('class_id').in_('class_id', class_ids).execute() if class_ids else type('obj', (object,), {'data': []})()
        tasks_count = {}
        for t in tasks_result.data:
            tasks_count[t['class_id']] = tasks_count.get(t['class_id'], 0) + 1

        # 4) Assemble response
        students = []
        for s in students_result.data:
            students.append({
                'id':             s['id'],
                'name':           s['name'],
                'city_name':      s.get('cities', {}).get('name', 'Unknown') if s.get('cities') else 'Unknown',
                'class_name':     s.get('classes', {}).get('name', 'Not Assigned') if s.get('classes') else 'Not Assigned',
                'total_points':   s['total_points'],
                'tasks_completed': approvals_count.get(s['id'], 0),
                'total_tasks':    tasks_count.get(s.get('class_id'), 0),
                'created_at':     s['created_at']
            })

        students.sort(key=lambda x: x['total_points'], reverse=True)
        return jsonify(students)

    except Exception as e:
        print(f"[get_students] Error: {e}")
        import traceback; traceback.print_exc()
        return jsonify([])


@app.route('/api/students', methods=['POST'])
def add_student():
    try:
        data = request.json
        supabase.table('students').insert({
            'name':         data['name'],
            'city_id':      data['city_id'],
            'class_id':     data.get('class_id'),
            'total_points': 0
        }).execute()
        _log('ADD_STUDENT', f"Added new student: {data['name']}", 'Admin')
        return jsonify({'success': True, 'message': 'Student added!'})
    except Exception as e:
        print(f"[add_student] Error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/students/<int:student_id>')
def get_student_details(student_id):
    try:
        student = supabase.table('students').select('*, cities(name), classes(name)').eq('id', student_id).single().execute()
        if not student.data:
            return jsonify({'student': None, 'approvals': []})

        s = student.data
        student_data = {
            **s,
            'city_name':  s.get('cities', {}).get('name', 'Unknown') if s.get('cities') else 'Unknown',
            'class_name': s.get('classes', {}).get('name', 'Not Assigned') if s.get('classes') else 'Not Assigned',
        }

        approvals = supabase.table('approvals').select('*, tasks(task_name, max_points)').eq('student_id', student_id).order('approval_date', desc=True).execute()

        return jsonify({'student': student_data, 'approvals': approvals.data})
    except Exception as e:
        print(f"[get_student_details] Error: {e}")
        return jsonify({'student': None, 'approvals': []})


# ── Approvals ────────────────────────────────────────────────────────────────

@app.route('/api/approvals', methods=['POST'])
def add_approval():
    try:
        data = request.json

        # Validate grade_points against max_points for this task
        task = supabase.table('tasks').select('max_points').eq('id', data['task_id']).single().execute()
        if task.data:
            max_pts = task.data['max_points']
            if not (0 <= data['grade_points'] <= max_pts):
                return jsonify({'success': False, 'error': f'grade_points must be between 0 and {max_pts}'}), 400

        # Find or create student
        existing = supabase.table('students').select('id, total_points').eq('name', data['student_name']).eq('city_id', data['city_id']).execute()

        if not existing.data:
            new_student = supabase.table('students').insert({
                'name':         data['student_name'],
                'city_id':      data['city_id'],
                'class_id':     data['class_id'],
                'total_points': 0
            }).execute()
            student_id    = new_student.data[0]['id']
            current_total = 0
        else:
            student_id    = existing.data[0]['id']
            current_total = existing.data[0]['total_points']

        # Add approval
        supabase.table('approvals').insert({
            'student_id':       student_id,
            'class_id':         data['class_id'],
            'task_id':          data['task_id'],
            'grade_points':     data['grade_points'],
            'mentor_signature': data['mentor_signature'],
            'approval_date':    data['approval_date']
        }).execute()

        # Update total points
        new_total = current_total + data['grade_points']
        supabase.table('students').update({'total_points': new_total}).eq('id', student_id).execute()

        _log('ADD_APPROVAL', f"Added {data['grade_points']} points for {data['student_name']} (Total: {new_total})", data['mentor_signature'])

        return jsonify({'success': True, 'student_total': new_total})
    except Exception as e:
        print(f"[add_approval] Error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/approvals/<int:approval_id>', methods=['DELETE'])
def delete_approval(approval_id):
    try:
        approval = supabase.table('approvals').select('student_id, grade_points').eq('id', approval_id).single().execute()
        if approval.data:
            student_id = approval.data['student_id']
            points     = approval.data['grade_points']

            supabase.table('approvals').delete().eq('id', approval_id).execute()

            student = supabase.table('students').select('total_points').eq('id', student_id).single().execute()
            if student.data:
                new_total = max(0, student.data['total_points'] - points)  # never go below 0
                supabase.table('students').update({'total_points': new_total}).eq('id', student_id).execute()

        return jsonify({'success': True})
    except Exception as e:
        print(f"[delete_approval] Error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 400


# ── Activity Log ─────────────────────────────────────────────────────────────

@app.route('/api/activity-log')
def get_activity_log():
    try:
        result = supabase.table('activity_log').select('*').order('timestamp', desc=True).limit(50).execute()
        return jsonify(result.data)
    except Exception as e:
        print(f"[get_activity_log] Error: {e}")
        return jsonify([])


# ── Excel Download ────────────────────────────────────────────────────────────

@app.route('/api/download-excel')
def download_excel():
    try:
        city_id = request.args.get('city_id', type=int)

        query = supabase.table('students').select('*, cities(name), classes(name)')
        if city_id:
            query = query.eq('city_id', city_id)
        students = query.execute()

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Students"

        headers = ['Student Name', 'City', 'Class', 'Total Points']
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill(start_color="0D6EFD", end_color="0D6EFD", fill_type="solid")

        for row, s in enumerate(students.data, 2):
            ws.cell(row=row, column=1, value=s['name'])
            ws.cell(row=row, column=2, value=s.get('cities', {}).get('name', 'Unknown') if s.get('cities') else 'Unknown')
            ws.cell(row=row, column=3, value=s.get('classes', {}).get('name', 'Not Assigned') if s.get('classes') else 'Not Assigned')
            ws.cell(row=row, column=4, value=s['total_points'])

        excel_file = io.BytesIO()
        wb.save(excel_file)
        excel_file.seek(0)

        # FIX: use correct MIME type for .xlsx files
        return send_file(
            excel_file,
            as_attachment=True,
            download_name=f'students_{datetime.now().strftime("%Y%m%d")}.xlsx',
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    except Exception as e:
        print(f"[download_excel] Error: {e}")
        return jsonify({'error': str(e)}), 500


# ── Helper ────────────────────────────────────────────────────────────────────

def _log(action_type: str, description: str, user_name: str):
    """Log an activity. Failures are printed but never crash the main request."""
    try:
        supabase.table('activity_log').insert({
            'action_type': action_type,
            'description': description,
            'user_name':   user_name
        }).execute()
    except Exception as e:
        print(f"[_log] Warning — could not write activity log: {e}")


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
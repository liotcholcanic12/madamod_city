import os
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file
from supabase import create_client, Client
from dotenv import load_dotenv
import io
import openpyxl
from openpyxl.styles import Font, PatternFill

# Load environment variables
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

@app.route('/api/cities')
def get_cities():
    try:
        result = supabase.table('cities').select('*').order('name').execute()
        return jsonify(result.data)
    except Exception as e:
        print(f"Error: {e}")
        return jsonify([])

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
        print(f"Error: {e}")
        return jsonify([])

@app.route('/api/tasks/<int:class_id>')
def get_tasks(class_id):
    try:
        result = supabase.table('tasks').select('*').eq('class_id', class_id).order('task_name').execute()
        return jsonify(result.data)
    except Exception as e:
        print(f"Error: {e}")
        return jsonify([])

@app.route('/api/students')
def get_students():
    try:
        city_id = request.args.get('city_id', type=int)
        
        # Get all students first
        query = supabase.table('students').select('*, cities(name), classes(name)')
        if city_id:
            query = query.eq('city_id', city_id)
        students = query.execute()
        
        # Process each student to add counts
        for student in students.data:
            # Get city name
            if student.get('cities'):
                student['city_name'] = student['cities']['name']
            else:
                student['city_name'] = 'Unknown'
            
            # Get class name
            if student.get('classes'):
                student['class_name'] = student['classes']['name']
            else:
                student['class_name'] = 'Not Assigned'
            
            # Count completed tasks
            approvals = supabase.table('approvals').select('id').eq('student_id', student['id']).execute()
            student['tasks_completed'] = len(approvals.data)
            
            # Count total tasks in class
            if student.get('class_id'):
                tasks = supabase.table('tasks').select('id').eq('class_id', student['class_id']).execute()
                student['total_tasks'] = len(tasks.data)
            else:
                student['total_tasks'] = 0
            
            # Remove nested objects
            if 'cities' in student:
                del student['cities']
            if 'classes' in student:
                del student['classes']
        
        # Sort by total points
        students.data.sort(key=lambda x: x.get('total_points', 0), reverse=True)
        return jsonify(students.data)
    except Exception as e:
        print(f"Error in get_students: {e}")
        return jsonify([])

@app.route('/api/students', methods=['POST'])
def add_student():
    try:
        data = request.json
        result = supabase.table('students').insert({
            'name': data['name'],
            'city_id': data['city_id'],
            'class_id': data.get('class_id'),
            'total_points': 0
        }).execute()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/approvals', methods=['POST'])
def add_approval():
    try:
        data = request.json
        
        # Find or create student
        existing = supabase.table('students').select('*').eq('name', data['student_name']).eq('city_id', data['city_id']).execute()
        
        if len(existing.data) == 0:
            new_student = supabase.table('students').insert({
                'name': data['student_name'],
                'city_id': data['city_id'],
                'class_id': data['class_id'],
                'total_points': 0
            }).execute()
            student_id = new_student.data[0]['id']
            current_total = 0
        else:
            student_id = existing.data[0]['id']
            current_total = existing.data[0]['total_points']
        
        # Add approval
        supabase.table('approvals').insert({
            'student_id': student_id,
            'class_id': data['class_id'],
            'task_id': data['task_id'],
            'grade_points': data['grade_points'],
            'mentor_signature': data['mentor_signature'],
            'approval_date': data['approval_date']
        }).execute()
        
        # Update total points
        new_total = current_total + data['grade_points']
        supabase.table('students').update({
            'total_points': new_total
        }).eq('id', student_id).execute()
        
        return jsonify({'success': True, 'student_total': new_total})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/students/<int:student_id>')
def get_student_details(student_id):
    try:
        student = supabase.table('students').select('*, cities(name), classes(name)').eq('id', student_id).execute()
        approvals = supabase.table('approvals').select('*, tasks(task_name, max_points)').eq('student_id', student_id).order('approval_date', desc=True).execute()
        
        if student.data:
            student_data = student.data[0]
            if student_data.get('cities'):
                student_data['city_name'] = student_data['cities']['name']
            if student_data.get('classes'):
                student_data['class_name'] = student_data['classes']['name']
        
        return jsonify({
            'student': student.data[0] if student.data else None,
            'approvals': approvals.data
        })
    except Exception as e:
        return jsonify({'student': None, 'approvals': []})

@app.route('/api/activity-log')
def get_activity_log():
    try:
        result = supabase.table('activity_log').select('*').order('timestamp', desc=True).limit(50).execute()
        return jsonify(result.data)
    except Exception as e:
        return jsonify([])

@app.route('/api/classes', methods=['POST'])
def add_class():
    try:
        data = request.json
        supabase.table('classes').insert({
            'city_id': data['city_id'],
            'name': data['name']
        }).execute()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/tasks', methods=['POST'])
def add_task():
    try:
        data = request.json
        supabase.table('tasks').insert({
            'class_id': data['class_id'],
            'task_name': data['task_name'],
            'max_points': data.get('max_points', 100)
        }).execute()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/approvals/<int:approval_id>', methods=['DELETE'])
def delete_approval(approval_id):
    try:
        approval = supabase.table('approvals').select('student_id, grade_points').eq('id', approval_id).execute()
        if approval.data:
            student_id = approval.data[0]['student_id']
            points = approval.data[0]['grade_points']
            
            supabase.table('approvals').delete().eq('id', approval_id).execute()
            
            student = supabase.table('students').select('total_points').eq('id', student_id).execute()
            if student.data:
                new_total = student.data[0]['total_points'] - points
                supabase.table('students').update({'total_points': new_total}).eq('id', student_id).execute()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

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
        
        for row, student in enumerate(students.data, 2):
            city_name = student.get('cities', {}).get('name', 'Unknown') if student.get('cities') else 'Unknown'
            class_name = student.get('classes', {}).get('name', 'Not Assigned') if student.get('classes') else 'Not Assigned'
            ws.cell(row=row, column=1, value=student['name'])
            ws.cell(row=row, column=2, value=city_name)
            ws.cell(row=row, column=3, value=class_name)
            ws.cell(row=row, column=4, value=student['total_points'])
        
        excel_file = io.BytesIO()
        wb.save(excel_file)
        excel_file.seek(0)
        
        return send_file(excel_file, as_attachment=True, download_name=f'students_{datetime.now().strftime("%Y%m%d")}.xlsx', mimetype='application/vnd.openpyxl')
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

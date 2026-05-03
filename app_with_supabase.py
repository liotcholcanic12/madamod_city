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
        
        # Get students with city names
        query = supabase.table('students').select('*, cities(name)')
        if city_id:
            query = query.eq('city_id', city_id)
        
        result = query.execute()
        students = []
        
        for s in result.data:
            # Get city name
            city_name = s.get('cities', {}).get('name', 'Unknown') if s.get('cities') else 'Unknown'
            
            # Get class name
            class_name = 'Not Assigned'
            if s.get('class_id'):
                class_result = supabase.table('classes').select('name').eq('id', s['class_id']).execute()
                if class_result.data:
                    class_name = class_result.data[0]['name']
            
            # Count completed tasks
            approvals = supabase.table('approvals').select('id').eq('student_id', s['id']).execute()
            tasks_completed = len(approvals.data)
            
            # Count total tasks in class
            total_tasks = 0
            if s.get('class_id'):
                tasks_result = supabase.table('tasks').select('id').eq('class_id', s['class_id']).execute()
                total_tasks = len(tasks_result.data)
            
            students.append({
                'id': s['id'],
                'name': s['name'],
                'city_name': city_name,
                'class_name': class_name,
                'total_points': s['total_points'],
                'tasks_completed': tasks_completed,
                'total_tasks': total_tasks,
                'created_at': s['created_at']
            })
        
        # Sort by total points descending
        students.sort(key=lambda x: x['total_points'], reverse=True)
        return jsonify(students)
        
    except Exception as e:
        print(f"Error in get_students: {e}")
        import traceback
        traceback.print_exc()
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
        
        # Log activity
        try:
            supabase.table('activity_log').insert({
                'action_type': 'ADD_STUDENT',
                'description': f"Added new student: {data['name']}",
                'user_name': 'Admin'
            }).execute()
        except:
            pass
        
        return jsonify({'success': True, 'message': 'Student added!'})
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
        
        # Log activity
        try:
            supabase.table('activity_log').insert({
                'action_type': 'ADD_APPROVAL',
                'description': f"Added {data['grade_points']} points for {data['student_name']} (Total: {new_total})",
                'user_name': data['mentor_signature']
            }).execute()
        except:
            pass
        
        return jsonify({'success': True, 'student_total': new_total})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/students/<int:student_id>')
def get_student_details(student_id):
    try:
        # Get student info
        student = supabase.table('students').select('*').eq('id', student_id).execute()
        if not student.data:
            return jsonify({'student': None, 'approvals': []})
        
        student_data = student.data[0]
        
        # Get city name
        city = supabase.table('cities').select('name').eq('id', student_data['city_id']).execute()
        student_data['city_name'] = city.data[0]['name'] if city.data else 'Unknown'
        
        # Get class name
        if student_data.get('class_id'):
            class_result = supabase.table('classes').select('name').eq('id', student_data['class_id']).execute()
            student_data['class_name'] = class_result.data[0]['name'] if class_result.data else 'Not Assigned'
        else:
            student_data['class_name'] = 'Not Assigned'
        
        # Get approvals with task details
        approvals = supabase.table('approvals').select('*, tasks(task_name, max_points)').eq('student_id', student_id).order('approval_date', desc=True).execute()
        
        return jsonify({
            'student': student_data,
            'approvals': approvals.data
        })
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'student': None, 'approvals': []})

@app.route('/api/activity-log')
def get_activity_log():
    try:
        result = supabase.table('activity_log').select('*').order('timestamp', desc=True).limit(50).execute()
        return jsonify(result.data)
    except Exception as e:
        print(f"Error: {e}")
        return jsonify([])

@app.route('/api/classes', methods=['POST'])
def add_class():
    try:
        data = request.json
        supabase.table('classes').insert({
            'city_id': data['city_id'],
            'name': data['name']
        }).execute()
        
        try:
            supabase.table('activity_log').insert({
                'action_type': 'ADD_CLASS',
                'description': f"Added new class: {data['name']}",
                'user_name': 'Admin'
            }).execute()
        except:
            pass
        
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
        
        try:
            supabase.table('activity_log').insert({
                'action_type': 'ADD_TASK',
                'description': f"Added new task: {data['task_name']}",
                'user_name': 'Admin'
            }).execute()
        except:
            pass
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/approvals/<int:approval_id>', methods=['DELETE'])
def delete_approval(approval_id):
    try:
        # Get approval info
        approval = supabase.table('approvals').select('student_id, grade_points').eq('id', approval_id).execute()
        if approval.data:
            student_id = approval.data[0]['student_id']
            points = approval.data[0]['grade_points']
            
            # Delete approval
            supabase.table('approvals').delete().eq('id', approval_id).execute()
            
            # Update student total
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
        
        # Get students
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
            ws.cell(row=row, column=1, value=student['name'])
            city_name = student.get('cities', {}).get('name', 'Unknown') if student.get('cities') else 'Unknown'
            ws.cell(row=row, column=2, value=city_name)
            class_name = student.get('classes', {}).get('name', 'Not Assigned') if student.get('classes') else 'Not Assigned'
            ws.cell(row=row, column=3, value=class_name)
            ws.cell(row=row, column=4, value=student['total_points'])
        
        excel_file = io.BytesIO()
        wb.save(excel_file)
        excel_file.seek(0)
        
        return send_file(excel_file, as_attachment=True, download_name=f'students_{datetime.now().strftime("%Y%m%d")}.xlsx', mimetype='application/vnd.openpyxl')
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
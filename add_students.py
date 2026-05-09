import sqlite3
import random
from datetime import datetime, timedelta

DATABASE = '/tmp/school_tasks.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def add_sample_students():
    print("📚 Adding 50 sample students...")
    
    conn = get_db()
    
    # First, check if we already have students
    cursor = conn.execute('SELECT COUNT(*) as count FROM students')
    existing_count = cursor.fetchone()['count']
    
    if existing_count > 10:
        print(f"⚠️  You already have {existing_count} students. Adding more...")
    
    # Students for Madamod (30 students)
    madamod_students = [
        # Mathematics 101 (class_id = 1)
        ('Emma Watson', 1, 1, 245),
        ('Liam Johnson', 1, 1, 189),
        ('Olivia Smith', 1, 1, 312),
        ('Noah Brown', 1, 1, 178),
        ('Ava Davis', 1, 1, 267),
        ('Ethan Wilson', 1, 1, 134),
        ('Sophia Martinez', 1, 1, 298),
        ('Mason Anderson', 1, 1, 156),
        ('Isabella Taylor', 1, 1, 223),
        ('Logan Thomas', 1, 1, 345),
        ('Mia Jackson', 1, 1, 278),
        ('Lucas White', 1, 1, 198),
        ('Amelia Harris', 1, 1, 312),
        ('Jackson Martin', 1, 1, 167),
        ('Harper Thompson', 1, 1, 234),
        # Physics 202 (class_id = 2)
        ('Aiden Garcia', 1, 2, 189),
        ('Evelyn Martinez', 1, 2, 256),
        ('Oliver Robinson', 1, 2, 145),
        ('Abigail Clark', 1, 2, 289),
        ('Elijah Rodriguez', 1, 2, 178),
        ('Emily Lewis', 1, 2, 234),
        ('Carter Lee', 1, 2, 167),
        ('Elizabeth Walker', 1, 2, 298),
        ('Grayson Hall', 1, 2, 145),
        ('Sofia Allen', 1, 2, 267),
        # Literature 105 (class_id = 3)
        ('Gabriel Young', 1, 3, 189),
        ('Avery King', 1, 3, 223),
        ('Julian Wright', 1, 3, 156),
        ('Ella Scott', 1, 3, 278),
        ('Levi Green', 1, 3, 198)
    ]
    
    # Students for المنشاة (20 students)
    mensha_students = [
        # الرياضيات (class_id = 4)
        ('أحمد محمد', 2, 4, 245),
        ('محمد علي', 2, 4, 189),
        ('فاطمة حسن', 2, 4, 312),
        ('نور حسين', 2, 4, 178),
        ('علي إبراهيم', 2, 4, 267),
        ('زهراء خالد', 2, 4, 134),
        ('مريم سعيد', 2, 4, 298),
        # العلوم (class_id = 5)
        ('يوسف عبدالله', 2, 5, 278),
        ('آية كريم', 2, 5, 198),
        ('حمزة رشيد', 2, 5, 312),
        ('ليلى جميل', 2, 5, 167),
        ('سارة منير', 2, 5, 234),
        ('عمر نادر', 2, 5, 189),
        ('كريمة طارق', 2, 5, 256),
        # اللغة العربية (class_id = 6)
        ('أمل سامي', 2, 6, 234),
        ('منى رامي', 2, 6, 167),
        ('هبة زكي', 2, 6, 298),
        ('سامر ناجي', 2, 6, 145),
        ('ندى عزمي', 2, 6, 267),
        ('رامي صلاح', 2, 6, 189)
    ]
    
    # Insert Madamod students
    madamod_count = 0
    for student in madamod_students:
        try:
            conn.execute('''
                INSERT OR IGNORE INTO students (name, city_id, class_id, total_points)
                VALUES (?, ?, ?, ?)
            ''', student)
            madamod_count += 1
        except Exception as e:
            print(f"  Error adding {student[0]}: {e}")
    
    # Insert Mensha students
    mensha_count = 0
    for student in mensha_students:
        try:
            conn.execute('''
                INSERT OR IGNORE INTO students (name, city_id, class_id, total_points)
                VALUES (?, ?, ?, ?)
            ''', student)
            mensha_count += 1
        except Exception as e:
            print(f"  Error adding {student[0]}: {e}")
    
    conn.commit()
    
    # Add some sample approvals to show completed tasks
    print("\n📝 Adding sample task completions...")
    
    # Get all students to add random approvals
    students = conn.execute('SELECT id, class_id FROM students LIMIT 20').fetchall()
    
    approvals_added = 0
    for student in students:
        # Get tasks for this student's class
        tasks = conn.execute('SELECT id, max_points FROM tasks WHERE class_id = ?', (student['class_id'],)).fetchall()
        
        if tasks:
            # Add 1-3 random approvals per student
            num_approvals = random.randint(1, 3)
            for _ in range(num_approvals):
                task = random.choice(tasks)
                points = random.randint(50, task['max_points'])
                date = (datetime.now() - timedelta(days=random.randint(1, 30))).strftime('%Y-%m-%d')
                mentor = random.choice(['Mr. Smith', 'Ms. Johnson', 'Dr. Williams', 'الأستاذ أحمد', 'الأستاذة نور'])
                
                try:
                    conn.execute('''
                        INSERT OR IGNORE INTO approvals (student_id, class_id, task_id, grade_points, mentor_signature, approval_date)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (student['id'], student['class_id'], task['id'], points, mentor, date))
                    approvals_added += 1
                except:
                    pass
    
    conn.commit()
    
    # Get final count
    cursor = conn.execute('SELECT COUNT(*) as count FROM students')
    final_count = cursor.fetchone()['count']
    
    conn.close()
    
    print("\n" + "="*50)
    print(f"✅ Successfully added {madamod_count} Madamod students")
    print(f"✅ Successfully added {mensha_count} المنشاة students")
    print(f"✅ Total students in database: {final_count}")
    print(f"✅ Added {approvals_added} sample task completions")
    print("="*50)
    print("\n🎉 Refresh your browser to see all the new students!")
    
    return final_count

if __name__ == "__main__":
    print("⚠️  Make sure your Flask app is running!")
    print("   (Run 'python app.py' in another terminal)\n")
    
    response = input("Is your app running? (y/n): ")
    if response.lower() == 'y':
        add_sample_students()
    else:
        print("\nPlease start your app first with: python app.py")
        print("Then run this script again.")
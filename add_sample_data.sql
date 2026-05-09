-- Insert more cities if needed (already have Madamod and المنشاة)

-- Insert 30 students for Madamod
INSERT OR IGNORE INTO students (name, city_id, class_id, total_points) VALUES
-- Mathematics 101 class (class_id = 1)
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

-- Physics 202 class (class_id = 2)
('Mia Jackson', 1, 2, 278),
('Lucas White', 1, 2, 198),
('Amelia Harris', 1, 2, 312),
('Jackson Martin', 1, 2, 167),
('Harper Thompson', 1, 2, 234),
('Aiden Garcia', 1, 2, 189),
('Evelyn Martinez', 1, 2, 256),
('Oliver Robinson', 1, 2, 145),
('Abigail Clark', 1, 2, 289),
('Elijah Rodriguez', 1, 2, 178),

-- Literature 105 class (class_id = 3)
('Emily Lewis', 1, 3, 234),
('Carter Lee', 1, 3, 167),
('Elizabeth Walker', 1, 3, 298),
('Grayson Hall', 1, 3, 145),
('Sofia Allen', 1, 3, 267),
('Gabriel Young', 1, 3, 189),
('Avery King', 1, 3, 223),
('Julian Wright', 1, 3, 156),
('Ella Scott', 1, 3, 278),
('Levi Green', 1, 3, 198);

-- Insert 20 students for المنشاة
INSERT OR IGNORE INTO students (name, city_id, class_id, total_points) VALUES
-- الرياضيات class (class_id = 4)
('أحمد محمد', 2, 4, 245),
('محمد علي', 2, 4, 189),
('فاطمة حسن', 2, 4, 312),
('نور حسين', 2, 4, 178),
('علي إبراهيم', 2, 4, 267),
('زهراء خالد', 2, 4, 134),
('مريم سعيد', 2, 4, 298),

-- العلوم class (class_id = 5)
('يوسف عبدالله', 2, 5, 278),
('آية كريم', 2, 5, 198),
('حمزة رشيد', 2, 5, 312),
('ليلى جميل', 2, 5, 167),
('سارة منير', 2, 5, 234),
('عمر نادر', 2, 5, 189),
('كريمة طارق', 2, 5, 256),

-- اللغة العربية class (class_id = 6)
('أمل سامي', 2, 6, 234),
('منى رامي', 2, 6, 167),
('هبة زكي', 2, 6, 298),
('سامر ناجي', 2, 6, 145),
('ندى عزمي', 2, 6, 267),
('رامي صلاح', 2, 6, 189);

-- Insert sample approvals for each student (to show completed tasks)
-- Mathematics 101 approvals
INSERT OR IGNORE INTO approvals (student_id, class_id, task_id, grade_points, mentor_signature, approval_date) VALUES
(1, 1, 1, 45, 'Mr. Smith', date('now', '-5 days')),
(1, 1, 2, 85, 'Mr. Smith', date('now', '-3 days')),
(2, 1, 1, 40, 'Ms. Johnson', date('now', '-7 days')),
(2, 1, 3, 70, 'Ms. Johnson', date('now', '-2 days')),
(3, 1, 2, 92, 'Mr. Smith', date('now', '-4 days')),
(3, 1, 1, 48, 'Dr. Williams', date('now', '-1 day'));

-- Physics 202 approvals
INSERT OR IGNORE INTO approvals (student_id, class_id, task_id, grade_points, mentor_signature, approval_date) VALUES
(11, 2, 4, 95, 'Prof. Brown', date('now', '-6 days')),
(11, 2, 5, 70, 'Prof. Brown', date('now', '-3 days')),
(12, 2, 4, 85, 'Mrs. Davis', date('now', '-8 days')),
(13, 2, 6, 90, 'Dr. Wilson', date('now', '-2 days'));

-- Arabic approvals
INSERT OR IGNORE INTO approvals (student_id, class_id, task_id, grade_points, mentor_signature, approval_date) VALUES
(41, 6, 16, 48, 'الأستاذ أحمد', date('now', '-4 days')),
(41, 6, 17, 72, 'الأستاذة نور', date('now', '-1 day')),
(42, 6, 16, 42, 'الأستاذ خالد', date('now', '-5 days')),
(43, 6, 18, 68, 'الأستاذة منى', date('now', '-3 days'));

-- Log the activity
INSERT OR IGNORE INTO activity_log (action_type, description, user_name) VALUES
('BULK_ADD', 'Added 50 sample students to the system', 'Admin');

DROP TABLE IF EXISTS approvals;
DROP TABLE IF EXISTS students;
DROP TABLE IF EXISTS tasks;
DROP TABLE IF EXISTS classes;
DROP TABLE IF EXISTS cities;
DROP TABLE IF EXISTS activity_log;

-- Cities/Locations table
CREATE TABLE IF NOT EXISTS cities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Classes table (now linked to cities)
CREATE TABLE IF NOT EXISTS classes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    city_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (city_id) REFERENCES cities (id) ON DELETE CASCADE,
    UNIQUE(city_id, name)
);

-- Students table (track cumulative points)
CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    city_id INTEGER NOT NULL,
    class_id INTEGER,
    total_points INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (city_id) REFERENCES cities (id),
    FOREIGN KEY (class_id) REFERENCES classes (id),
    UNIQUE(name, city_id)  -- Same name can exist in different cities
);

-- Tasks table (different per class)
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    class_id INTEGER NOT NULL,
    task_name TEXT NOT NULL,
    max_points INTEGER DEFAULT 100,
    FOREIGN KEY (class_id) REFERENCES classes (id) ON DELETE CASCADE,
    UNIQUE(class_id, task_name)
);

-- Student task approvals (individual records)
CREATE TABLE IF NOT EXISTS approvals (
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
);

-- Activity log table
CREATE TABLE IF NOT EXISTS activity_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    action_type TEXT NOT NULL,
    description TEXT NOT NULL,
    user_name TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for faster lookups
CREATE INDEX IF NOT EXISTS idx_approvals_date ON approvals(approval_date);
CREATE INDEX IF NOT EXISTS idx_approvals_student ON approvals(student_id);
CREATE INDEX IF NOT EXISTS idx_activity_timestamp ON activity_log(timestamp);
CREATE INDEX IF NOT EXISTS idx_students_city ON students(city_id);
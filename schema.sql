-- Classes table
CREATE TABLE IF NOT EXISTS classes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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

-- Student task approvals
CREATE TABLE IF NOT EXISTS approvals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_name TEXT NOT NULL,
    class_id INTEGER NOT NULL,
    task_id INTEGER NOT NULL,
    grade_points INTEGER NOT NULL,
    mentor_signature TEXT NOT NULL,
    approval_date DATE NOT NULL,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
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
CREATE INDEX IF NOT EXISTS idx_approvals_student ON approvals(student_name);
CREATE INDEX IF NOT EXISTS idx_activity_timestamp ON activity_log(timestamp);
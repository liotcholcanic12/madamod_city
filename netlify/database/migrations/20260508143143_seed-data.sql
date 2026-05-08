INSERT INTO cities (name) VALUES ('Madamod'), ('المنشاة') ON CONFLICT (name) DO NOTHING;

INSERT INTO classes (city_id, name)
SELECT c.id, 'Mathematics 101' FROM cities c WHERE c.name = 'Madamod'
ON CONFLICT (city_id, name) DO NOTHING;

INSERT INTO classes (city_id, name)
SELECT c.id, 'Physics 202' FROM cities c WHERE c.name = 'Madamod'
ON CONFLICT (city_id, name) DO NOTHING;

INSERT INTO classes (city_id, name)
SELECT c.id, 'Literature 105' FROM cities c WHERE c.name = 'Madamod'
ON CONFLICT (city_id, name) DO NOTHING;

INSERT INTO classes (city_id, name)
SELECT c.id, 'الرياضيات' FROM cities c WHERE c.name = 'المنشاة'
ON CONFLICT (city_id, name) DO NOTHING;

INSERT INTO classes (city_id, name)
SELECT c.id, 'العلوم' FROM cities c WHERE c.name = 'المنشاة'
ON CONFLICT (city_id, name) DO NOTHING;

INSERT INTO classes (city_id, name)
SELECT c.id, 'اللغة العربية' FROM cities c WHERE c.name = 'المنشاة'
ON CONFLICT (city_id, name) DO NOTHING;

INSERT INTO tasks (class_id, task_name, max_points)
SELECT cl.id, 'Algebra Worksheet', 50 FROM classes cl WHERE cl.name = 'Mathematics 101'
ON CONFLICT (class_id, task_name) DO NOTHING;

INSERT INTO tasks (class_id, task_name, max_points)
SELECT cl.id, 'Calculus Problems', 100 FROM classes cl WHERE cl.name = 'Mathematics 101'
ON CONFLICT (class_id, task_name) DO NOTHING;

INSERT INTO tasks (class_id, task_name, max_points)
SELECT cl.id, 'Newton''s Laws Lab', 100 FROM classes cl WHERE cl.name = 'Physics 202'
ON CONFLICT (class_id, task_name) DO NOTHING;

INSERT INTO tasks (class_id, task_name, max_points)
SELECT cl.id, 'Shakespeare Essay', 100 FROM classes cl WHERE cl.name = 'Literature 105'
ON CONFLICT (class_id, task_name) DO NOTHING;

INSERT INTO tasks (class_id, task_name, max_points)
SELECT cl.id, 'ورقة عمل', 50 FROM classes cl WHERE cl.name = 'الرياضيات'
ON CONFLICT (class_id, task_name) DO NOTHING;

INSERT INTO tasks (class_id, task_name, max_points)
SELECT cl.id, 'تجربة علمية', 100 FROM classes cl WHERE cl.name = 'العلوم'
ON CONFLICT (class_id, task_name) DO NOTHING;

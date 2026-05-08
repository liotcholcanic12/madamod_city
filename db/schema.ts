import { pgTable, serial, text, timestamp, integer, date, unique } from "drizzle-orm/pg-core";

export const cities = pgTable("cities", {
  id: serial().primaryKey(),
  name: text().notNull().unique(),
  createdAt: timestamp("created_at").defaultNow(),
});

export const classes = pgTable("classes", {
  id: serial().primaryKey(),
  cityId: integer("city_id").notNull().references(() => cities.id),
  name: text().notNull(),
  createdAt: timestamp("created_at").defaultNow(),
}, (t) => [
  unique().on(t.cityId, t.name),
]);

export const students = pgTable("students", {
  id: serial().primaryKey(),
  name: text().notNull(),
  cityId: integer("city_id").notNull().references(() => cities.id),
  classId: integer("class_id").references(() => classes.id),
  totalPoints: integer("total_points").default(0),
  createdAt: timestamp("created_at").defaultNow(),
}, (t) => [
  unique().on(t.name, t.cityId),
]);

export const tasks = pgTable("tasks", {
  id: serial().primaryKey(),
  classId: integer("class_id").notNull().references(() => classes.id, { onDelete: "cascade" }),
  taskName: text("task_name").notNull(),
  maxPoints: integer("max_points").default(100),
}, (t) => [
  unique().on(t.classId, t.taskName),
]);

export const approvals = pgTable("approvals", {
  id: serial().primaryKey(),
  studentId: integer("student_id").notNull().references(() => students.id),
  classId: integer("class_id").notNull().references(() => classes.id),
  taskId: integer("task_id").notNull().references(() => tasks.id),
  gradePoints: integer("grade_points").notNull(),
  mentorSignature: text("mentor_signature").notNull(),
  approvalDate: date("approval_date").notNull(),
  notes: text(),
  createdAt: timestamp("created_at").defaultNow(),
});

export const activityLog = pgTable("activity_log", {
  id: serial().primaryKey(),
  actionType: text("action_type").notNull(),
  description: text().notNull(),
  userName: text("user_name"),
  timestamp: timestamp().defaultNow(),
});

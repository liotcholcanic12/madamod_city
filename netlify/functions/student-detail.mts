import type { Config } from "@netlify/functions";
import { db } from "../../db/index.js";
import { students, cities, classes, approvals, tasks } from "../../db/schema.js";
import { eq, desc } from "drizzle-orm";

export default async (req: Request, context: any) => {
  if (req.method === "GET") {
    const studentId = parseInt(context.params?.id);
    if (!studentId) return Response.json({ error: "Invalid id" }, { status: 400 });

    const [student] = await db
      .select({
        id: students.id,
        name: students.name,
        city_id: students.cityId,
        class_id: students.classId,
        total_points: students.totalPoints,
        created_at: students.createdAt,
        city_name: cities.name,
        class_name: classes.name,
      })
      .from(students)
      .innerJoin(cities, eq(students.cityId, cities.id))
      .leftJoin(classes, eq(students.classId, classes.id))
      .where(eq(students.id, studentId));

    const approvalRows = await db
      .select({
        id: approvals.id,
        student_id: approvals.studentId,
        class_id: approvals.classId,
        task_id: approvals.taskId,
        grade_points: approvals.gradePoints,
        mentor_signature: approvals.mentorSignature,
        approval_date: approvals.approvalDate,
        notes: approvals.notes,
        created_at: approvals.createdAt,
        tasks: {
          task_name: tasks.taskName,
          max_points: tasks.maxPoints,
        },
      })
      .from(approvals)
      .innerJoin(tasks, eq(approvals.taskId, tasks.id))
      .where(eq(approvals.studentId, studentId))
      .orderBy(desc(approvals.approvalDate));

    return Response.json({
      student: student ?? null,
      approvals: approvalRows,
    });
  }

  return new Response("Method not allowed", { status: 405 });
};

export const config: Config = {
  path: "/api/students/:id",
  method: "GET",
};

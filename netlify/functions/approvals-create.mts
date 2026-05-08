import type { Config } from "@netlify/functions";
import { db } from "../../db/index.js";
import { students, approvals, activityLog } from "../../db/schema.js";
import { eq, and } from "drizzle-orm";

export default async (req: Request) => {
  if (req.method === "POST") {
    try {
      const data = await req.json();

      const existing = await db
        .select({ id: students.id, totalPoints: students.totalPoints })
        .from(students)
        .where(and(eq(students.name, data.student_name), eq(students.cityId, data.city_id)));

      let studentId: number;
      let currentTotal: number;

      if (existing.length === 0) {
        const [inserted] = await db
          .insert(students)
          .values({ name: data.student_name, cityId: data.city_id, classId: data.class_id, totalPoints: 0 })
          .returning({ id: students.id });
        studentId = inserted.id;
        currentTotal = 0;
      } else {
        studentId = existing[0].id;
        currentTotal = existing[0].totalPoints ?? 0;
      }

      await db.insert(approvals).values({
        studentId,
        classId: data.class_id,
        taskId: data.task_id,
        gradePoints: data.grade_points,
        mentorSignature: data.mentor_signature,
        approvalDate: data.approval_date,
      });

      const newTotal = currentTotal + data.grade_points;
      await db.update(students).set({ totalPoints: newTotal }).where(eq(students.id, studentId));

      await db.insert(activityLog).values({
        actionType: "ADD_APPROVAL",
        description: `Added ${data.grade_points} points for ${data.student_name}`,
        userName: data.mentor_signature,
      });

      return Response.json({ success: true, student_total: newTotal });
    } catch (err: any) {
      return Response.json({ success: false, error: err.message }, { status: 400 });
    }
  }

  return new Response("Method not allowed", { status: 405 });
};

export const config: Config = {
  path: "/api/approvals",
  method: "POST",
};

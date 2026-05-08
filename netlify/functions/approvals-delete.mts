import type { Config } from "@netlify/functions";
import { db } from "../../db/index.js";
import { approvals, students } from "../../db/schema.js";
import { eq } from "drizzle-orm";

export default async (req: Request, context: any) => {
  if (req.method === "DELETE") {
    try {
      const approvalId = parseInt(context.params?.id);
      if (!approvalId) return Response.json({ error: "Invalid id" }, { status: 400 });

      const [approval] = await db
        .select({ studentId: approvals.studentId, gradePoints: approvals.gradePoints })
        .from(approvals)
        .where(eq(approvals.id, approvalId));

      if (approval) {
        await db.delete(approvals).where(eq(approvals.id, approvalId));
        const [student] = await db
          .select({ totalPoints: students.totalPoints })
          .from(students)
          .where(eq(students.id, approval.studentId));
        const newTotal = Math.max(0, (student?.totalPoints ?? 0) - approval.gradePoints);
        await db.update(students).set({ totalPoints: newTotal }).where(eq(students.id, approval.studentId));
      }

      return Response.json({ success: true });
    } catch (err: any) {
      return Response.json({ success: false, error: err.message }, { status: 400 });
    }
  }

  return new Response("Method not allowed", { status: 405 });
};

export const config: Config = {
  path: "/api/approvals/:id",
  method: "DELETE",
};

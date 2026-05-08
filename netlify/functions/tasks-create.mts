import type { Config } from "@netlify/functions";
import { db } from "../../db/index.js";
import { tasks } from "../../db/schema.js";

export default async (req: Request) => {
  if (req.method === "POST") {
    try {
      const data = await req.json();
      await db.insert(tasks).values({
        classId: data.class_id,
        taskName: data.task_name,
        maxPoints: data.max_points ?? 100,
      });
      return Response.json({ success: true });
    } catch (err: any) {
      return Response.json({ success: false, error: err.message }, { status: 400 });
    }
  }
  return new Response("Method not allowed", { status: 405 });
};

export const config: Config = {
  path: "/api/tasks",
  method: "POST",
};

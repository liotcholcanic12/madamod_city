import type { Config } from "@netlify/functions";
import { db } from "../../db/index.js";
import { tasks } from "../../db/schema.js";
import { eq, asc } from "drizzle-orm";

export default async (req: Request, context: any) => {
  if (req.method === "GET") {
    const classId = context.params?.class_id;
    if (!classId) {
      return Response.json({ error: "class_id required" }, { status: 400 });
    }
    const result = await db.select().from(tasks).where(eq(tasks.classId, parseInt(classId))).orderBy(asc(tasks.taskName));
    return Response.json(result);
  }
  return new Response("Method not allowed", { status: 405 });
};

export const config: Config = {
  path: "/api/tasks/:class_id",
  method: "GET",
};

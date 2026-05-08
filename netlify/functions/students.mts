import type { Config } from "@netlify/functions";
import { db } from "../../db/index.js";
import { students, cities, classes } from "../../db/schema.js";
import { eq, and, desc, sql } from "drizzle-orm";

export default async (req: Request) => {
  if (req.method === "GET") {
    const url = new URL(req.url);
    const cityId = url.searchParams.get("city_id");
    const classId = url.searchParams.get("class_id");

    const conditions = [];
    if (cityId) conditions.push(eq(students.cityId, parseInt(cityId)));
    if (classId) conditions.push(eq(students.classId, parseInt(classId)));

    const whereClause = conditions.length === 0 ? undefined
      : conditions.length === 1 ? conditions[0]
      : and(...conditions);

    const result = await db
      .select({
        id: students.id,
        name: students.name,
        city_id: students.cityId,
        class_id: students.classId,
        total_points: students.totalPoints,
        created_at: students.createdAt,
        city_name: cities.name,
        class_name: classes.name,
        tasks_completed: sql<number>`(SELECT COUNT(*) FROM approvals WHERE approvals.student_id = ${students.id})`,
        total_tasks: sql<number>`(SELECT COUNT(*) FROM tasks WHERE tasks.class_id = ${students.classId})`,
      })
      .from(students)
      .innerJoin(cities, eq(students.cityId, cities.id))
      .leftJoin(classes, eq(students.classId, classes.id))
      .where(whereClause)
      .orderBy(desc(students.totalPoints));

    return Response.json(result);
  }

  if (req.method === "POST") {
    try {
      const data = await req.json();
      await db.insert(students).values({
        name: data.name,
        cityId: data.city_id,
        classId: data.class_id ?? null,
        totalPoints: 0,
      });
      return Response.json({ success: true });
    } catch (err: any) {
      return Response.json({ success: false, error: err.message }, { status: 400 });
    }
  }

  return new Response("Method not allowed", { status: 405 });
};

export const config: Config = {
  path: "/api/students",
};

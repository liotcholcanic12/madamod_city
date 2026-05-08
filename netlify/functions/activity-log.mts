import type { Config } from "@netlify/functions";
import { db } from "../../db/index.js";
import { activityLog } from "../../db/schema.js";
import { desc } from "drizzle-orm";

export default async (req: Request) => {
  if (req.method === "GET") {
    const logs = await db.select().from(activityLog).orderBy(desc(activityLog.timestamp)).limit(50);
    return Response.json(logs);
  }
  return new Response("Method not allowed", { status: 405 });
};

export const config: Config = {
  path: "/api/activity-log",
  method: "GET",
};

import type { Config } from "@netlify/functions";
import { db } from "../../db/index.js";
import { cities } from "../../db/schema.js";
import { asc } from "drizzle-orm";

export default async (req: Request) => {
  if (req.method === "GET") {
    const result = await db.select().from(cities).orderBy(asc(cities.name));
    return Response.json(result);
  }
  return new Response("Method not allowed", { status: 405 });
};

export const config: Config = {
  path: "/api/cities",
};

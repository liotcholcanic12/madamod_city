import type { Config } from "@netlify/functions";
import { db } from "../../db/index.js";
import { classes } from "../../db/schema.js";
import { eq, asc } from "drizzle-orm";

export default async (req: Request) => {
  if (req.method === "GET") {
    const url = new URL(req.url);
    const cityId = url.searchParams.get("city_id");
    let result;
    if (cityId) {
      result = await db.select().from(classes).where(eq(classes.cityId, parseInt(cityId))).orderBy(asc(classes.name));
    } else {
      result = await db.select().from(classes).orderBy(asc(classes.name));
    }
    return Response.json(result);
  }

  if (req.method === "POST") {
    try {
      const data = await req.json();
      await db.insert(classes).values({ cityId: data.city_id, name: data.name });
      return Response.json({ success: true });
    } catch (err: any) {
      return Response.json({ success: false, error: err.message }, { status: 400 });
    }
  }

  return new Response("Method not allowed", { status: 405 });
};

export const config: Config = {
  path: "/api/classes",
};

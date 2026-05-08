import type { Config } from "@netlify/functions";
import { db } from "../../db/index.js";
import { students, cities, classes } from "../../db/schema.js";
import { eq, desc } from "drizzle-orm";
import ExcelJS from "exceljs";

export default async (req: Request) => {
  if (req.method === "GET") {
    try {
      const url = new URL(req.url);
      const cityId = url.searchParams.get("city_id");

      let query = db
        .select({
          name: students.name,
          city_name: cities.name,
          class_name: classes.name,
          total_points: students.totalPoints,
        })
        .from(students)
        .innerJoin(cities, eq(students.cityId, cities.id))
        .leftJoin(classes, eq(students.classId, classes.id))
        .orderBy(desc(students.totalPoints));

      const data = cityId
        ? await query.where(eq(students.cityId, parseInt(cityId)))
        : await query;

      const workbook = new ExcelJS.Workbook();
      const ws = workbook.addWorksheet("Students");

      ws.columns = [
        { header: "Student Name", key: "name", width: 30 },
        { header: "City", key: "city_name", width: 20 },
        { header: "Class", key: "class_name", width: 25 },
        { header: "Total Points", key: "total_points", width: 15 },
      ];

      ws.getRow(1).eachCell((cell) => {
        cell.font = { bold: true, color: { argb: "FFFFFFFF" } };
        cell.fill = { type: "pattern", pattern: "solid", fgColor: { argb: "FF0D6EFD" } };
      });

      data.forEach((row) => {
        ws.addRow({
          name: row.name,
          city_name: row.city_name,
          class_name: row.class_name ?? "Not Assigned",
          total_points: row.total_points ?? 0,
        });
      });

      const buffer = await workbook.xlsx.writeBuffer();
      const date = new Date().toISOString().slice(0, 10).replace(/-/g, "");

      return new Response(buffer as ArrayBuffer, {
        headers: {
          "Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
          "Content-Disposition": `attachment; filename="students_${date}.xlsx"`,
        },
      });
    } catch (err: any) {
      return Response.json({ error: err.message }, { status: 500 });
    }
  }

  return new Response("Method not allowed", { status: 405 });
};

export const config: Config = {
  path: "/api/download-excel",
  method: "GET",
};

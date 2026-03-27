import { NextResponse } from "next/server";
import pool from "@/lib/db";

export async function GET() {
  const client = await pool.connect();
  try {
    const { rows } = await client.query(`
      SELECT
        r.id, r.topic, r.url, r.title, r.content, r.labeled, r.created_at,
        (SELECT l.labels FROM labels l WHERE l.result_id = r.id ORDER BY l.created_at DESC LIMIT 1) AS labels
      FROM results r
      ORDER BY r.created_at DESC
      LIMIT 50
    `);
    return NextResponse.json(rows);
  } catch (err) {
    console.error("route error:", err);
    return NextResponse.json({ error: "Internal server error" }, { status: 500 });
  } finally {
    client.release();
  }
}

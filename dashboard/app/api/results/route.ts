import { NextResponse } from "next/server";
import pool from "@/lib/db";

export async function GET() {
  const client = await pool.connect();
  try {
    const { rows } = await client.query(`
      SELECT
        r.id, r.topic, r.url, r.title, r.content, r.labeled, r.created_at,
        l.labels
      FROM results r
      LEFT JOIN labels l ON l.result_id = r.id
      ORDER BY r.created_at DESC
      LIMIT 50
    `);
    return NextResponse.json(rows);
  } finally {
    client.release();
  }
}

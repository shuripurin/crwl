import { NextResponse } from "next/server";
import pool from "@/lib/db";

export async function GET() {
  const client = await pool.connect();
  try {
    const [counts, agents, logs] = await Promise.all([
      client.query<{ total: string; labeled: string; unlabeled: string }>(`
        SELECT
          COUNT(*)::text AS total,
          COUNT(*) FILTER (WHERE labeled = true)::text AS labeled,
          COUNT(*) FILTER (WHERE labeled = false)::text AS unlabeled
        FROM results
      `),
      client.query<{ agent_id: string; agent_type: string; status: string; updated_at: string }>(`
        SELECT DISTINCT ON (agent_id)
          agent_id, agent_type, status, created_at AS updated_at
        FROM agent_logs
        ORDER BY agent_id, created_at DESC
      `),
      client.query<{ agent_id: string; agent_type: string; status: string; message: string; created_at: string }>(`
        SELECT agent_id, agent_type, status, message, created_at
        FROM agent_logs
        ORDER BY created_at DESC
        LIMIT 20
      `),
    ]);

    const { total, labeled, unlabeled } = counts.rows[0] ?? { total: "0", labeled: "0", unlabeled: "0" };

    return NextResponse.json({
      total: Number(total),
      labeled: Number(labeled),
      unlabeled: Number(unlabeled),
      agents: agents.rows,
      recent_logs: logs.rows,
    });
  } finally {
    client.release();
  }
}

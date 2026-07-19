import { asc, desc, eq, inArray } from "drizzle-orm";
import { getDb } from "../../../db";
import { productResearchMissions } from "../../../db/schema";

export type ResearchMissionStatus = "queued" | "researching" | "review" | "needs_input" | "blocked" | "archived";

export type ResearchMissionInput = {
  goal: string;
  marketplaces: string[];
  category: string;
  maxPrice: number | null;
  timeframe: string;
  resultLimit: number;
  targetChannel: string;
};

export type ResearchMissionWorkerResult = {
  missionId: string;
  status: "review" | "needs_input" | "blocked";
  report: Record<string, unknown>;
  error: string;
};

export async function createResearchMission(input: ResearchMissionInput) {
  const db = getDb();
  await ensureSchema();
  const now = new Date().toISOString();
  await db.insert(productResearchMissions).values({
    id: crypto.randomUUID(),
    goal: input.goal,
    marketplaces: JSON.stringify(input.marketplaces),
    category: input.category,
    maxPriceCents: input.maxPrice == null ? null : Math.round(input.maxPrice * 100),
    timeframe: input.timeframe,
    resultLimit: input.resultLimit,
    targetChannel: input.targetChannel,
    status: "queued",
    result: "{}",
    error: "",
    createdAt: now,
    updatedAt: now,
  });
  return researchMissionState();
}

export async function researchMissionState() {
  const db = getDb();
  await ensureSchema();
  const rows = await db.select().from(productResearchMissions).orderBy(desc(productResearchMissions.updatedAt)).limit(30);
  return { missions: rows.filter((row) => row.status !== "archived").map(publicMission) };
}

export async function archiveResearchMission(missionId: string) {
  const db = getDb();
  await ensureSchema();
  const existing = await db.select().from(productResearchMissions).where(eq(productResearchMissions.id, missionId)).limit(1);
  if (!existing[0]) throw new Error("Research mission was not found");
  await db.update(productResearchMissions).set({
    status: "archived",
    updatedAt: new Date().toISOString(),
  }).where(eq(productResearchMissions.id, missionId));
  return researchMissionState();
}

export async function researchMissionQueue() {
  const db = getDb();
  await ensureSchema();
  const rows = await db.select().from(productResearchMissions)
    .where(inArray(productResearchMissions.status, ["queued", "researching"]))
    .orderBy(asc(productResearchMissions.createdAt)).limit(5);
  return { missions: rows.map(publicMission) };
}

export async function applyResearchMissionResult(input: ResearchMissionWorkerResult) {
  const db = getDb();
  await ensureSchema();
  const existing = await db.select().from(productResearchMissions).where(eq(productResearchMissions.id, input.missionId)).limit(1);
  if (!existing[0]) throw new Error("Research mission was not found");
  await db.update(productResearchMissions).set({
    status: input.status,
    result: JSON.stringify(input.report),
    error: input.error,
    updatedAt: new Date().toISOString(),
  }).where(eq(productResearchMissions.id, input.missionId));
  return researchMissionState();
}

async function ensureSchema() {
  const { env } = await import("cloudflare:workers");
  await env.DB.prepare("CREATE TABLE IF NOT EXISTS product_research_missions (id TEXT PRIMARY KEY, goal TEXT NOT NULL, marketplaces TEXT NOT NULL, category TEXT NOT NULL, max_price_cents INTEGER, timeframe TEXT NOT NULL, result_limit INTEGER NOT NULL, target_channel TEXT NOT NULL, status TEXT NOT NULL, result TEXT NOT NULL, error TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL)").run();
  await env.DB.prepare("CREATE INDEX IF NOT EXISTS product_research_mission_status_idx ON product_research_missions(status)").run();
}

function publicMission(row: typeof productResearchMissions.$inferSelect) {
  let marketplaces: string[] = [];
  let result: Record<string, unknown> = {};
  try { marketplaces = JSON.parse(row.marketplaces) as string[]; } catch { marketplaces = []; }
  try { result = JSON.parse(row.result) as Record<string, unknown>; } catch { result = {}; }
  return {
    id: row.id,
    goal: row.goal,
    marketplaces,
    category: row.category,
    maxPrice: row.maxPriceCents == null ? null : row.maxPriceCents / 100,
    timeframe: row.timeframe,
    resultLimit: row.resultLimit,
    targetChannel: row.targetChannel,
    status: row.status as ResearchMissionStatus,
    result,
    error: row.error,
    providerStatus: "not_called",
    publicationStatus: "blocked",
    createdAt: row.createdAt,
    updatedAt: row.updatedAt,
  };
}

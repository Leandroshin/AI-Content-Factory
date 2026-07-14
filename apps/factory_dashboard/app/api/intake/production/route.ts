import { requireDashboardIntake } from "../_shared";
import { applyProductionWorkerResult, productionWorkerQueue, type ProductionWorkerResult } from "../../dashboard/store";

const MAX_BODY_BYTES = 16_000;

export async function GET(request: Request) {
  const unauthorized = await requireDashboardIntake(request, "Production worker");
  if (unauthorized) return unauthorized;
  return Response.json(await productionWorkerQueue());
}

export async function POST(request: Request) {
  const unauthorized = await requireDashboardIntake(request, "Production worker");
  if (unauthorized) return unauthorized;
  const raw = await request.text();
  if (new TextEncoder().encode(raw).byteLength > MAX_BODY_BYTES) return Response.json({ error: "Payload too large" }, { status: 413 });
  try {
    const input = validateResult(JSON.parse(raw) as unknown);
    return Response.json({ accepted: true, state: await applyProductionWorkerResult(input) }, { status: 202 });
  } catch (error) {
    return Response.json({ error: error instanceof Error ? error.message : "Invalid payload" }, { status: 400 });
  }
}

function validateResult(value: unknown): ProductionWorkerResult {
  if (!value || typeof value !== "object") throw new Error("Payload must be an object");
  const item = value as Record<string, unknown>;
  const status = text(item.status, "status", 20);
  if (status !== "review" && status !== "failed") throw new Error("status is invalid");
  const assets = Array.isArray(item.assetPlan) ? item.assetPlan.map((entry) => text(entry, "assetPlan", 240)) : [];
  if (assets.length > 12) throw new Error("assetPlan is too large");
  return {
    opportunityId: text(item.opportunityId, "opportunityId", 100),
    status,
    hook: optionalText(item.hook, "hook", 300),
    script: optionalText(item.script, "script", 6_000),
    callToAction: optionalText(item.callToAction, "callToAction", 300),
    assetPlan: assets,
    reviewNotes: text(item.reviewNotes, "reviewNotes", 1_000),
  };
}

function text(value: unknown, name: string, max: number) {
  if (typeof value !== "string" || !value.trim() || value.length > max) throw new Error(`${name} is invalid`);
  return value.trim();
}

function optionalText(value: unknown, name: string, max: number) {
  if (value == null || value === "") return "";
  return text(value, name, max);
}

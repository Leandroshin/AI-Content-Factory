import { requireDashboardIntake } from "../_shared";
import { applyMediaProductionWorkerResult, mediaProductionWorkerQueue, type MediaProductionWorkerResult } from "../../dashboard/store";

const MAX_BODY_BYTES = 12_000;

export async function GET(request: Request) {
  const unauthorized = await requireDashboardIntake(request, "Media production worker");
  if (unauthorized) return unauthorized;
  return Response.json(await mediaProductionWorkerQueue());
}

export async function POST(request: Request) {
  const unauthorized = await requireDashboardIntake(request, "Media production worker");
  if (unauthorized) return unauthorized;
  const raw = await request.text();
  if (new TextEncoder().encode(raw).byteLength > MAX_BODY_BYTES) return Response.json({ error: "Payload too large" }, { status: 413 });
  try {
    const input = validate(JSON.parse(raw) as unknown);
    return Response.json({ accepted: true, state: await applyMediaProductionWorkerResult(input) }, { status: 202 });
  } catch (error) {
    return Response.json({ error: error instanceof Error ? error.message : "Invalid payload" }, { status: 400 });
  }
}

function validate(value: unknown): MediaProductionWorkerResult {
  if (!value || typeof value !== "object") throw new Error("Payload must be an object");
  const item = value as Record<string, unknown>;
  const opportunityId = required(item.opportunityId, "opportunityId", 100);
  const status = required(item.status, "status", 30);
  if (status !== "media_review" && status !== "failed") throw new Error("status is invalid");
  const rawDepartments = item.departments && typeof item.departments === "object" ? item.departments as Record<string, unknown> : {};
  const departments: MediaProductionWorkerResult["departments"] = {};
  for (const key of ["audio", "image", "video"]) {
    const raw = rawDepartments[key];
    if (!raw || typeof raw !== "object") continue;
    const part = raw as Record<string, unknown>;
    departments[key] = { label: required(part.label, `${key}.label`, 40), status: required(part.status, `${key}.status`, 20), summary: required(part.summary, `${key}.summary`, 500), qualityPassed: part.qualityPassed === true };
  }
  return { opportunityId, status, reviewNotes: required(item.reviewNotes, "reviewNotes", 1000), departments, qualityPassed: item.qualityPassed === true, publicationStatus: "blocked", providerStatus: "not_called", finalAssetStatus: "not_generated" };
}

function required(value: unknown, name: string, max: number) {
  if (typeof value !== "string" || !value.trim() || value.length > max) throw new Error(`${name} is invalid`);
  return value.trim();
}

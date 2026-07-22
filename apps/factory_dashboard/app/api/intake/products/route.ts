import { requireDashboardIntake } from "../_shared";
import { applyProductWorkerResult, productWorkerQueue, type ProductWorkerResult } from "../../products/store";

const MAX_BODY_BYTES = 24_000;
const DYNAMIC_RESPONSE = { headers: { "Cache-Control": "no-store" } };

export async function GET(request: Request) {
  const unauthorized = await requireDashboardIntake(request, "Product worker");
  if (unauthorized) return unauthorized;
  return Response.json(await productWorkerQueue(), DYNAMIC_RESPONSE);
}

export async function POST(request: Request) {
  const unauthorized = await requireDashboardIntake(request, "Product worker");
  if (unauthorized) return unauthorized;
  const raw = await request.text();
  if (new TextEncoder().encode(raw).byteLength > MAX_BODY_BYTES) return Response.json({ error: "Payload too large" }, { status: 413 });
  try {
    const input = validateResult(JSON.parse(raw) as unknown);
    const state = await applyProductWorkerResult(input);
    const product = state.items.find((item) => item.id === input.requestId);
    let telegramCandidatePrepared = false;
    if (product?.campaignPackage?.status === "draft_ready" && product.targetChannel === "telegram_public") {
      const { queueTelegramPublication } = await import("../../telegram-publications/store");
      await queueTelegramPublication(input.requestId);
      telegramCandidatePrepared = true;
    }
    return Response.json(
      { accepted: true, state, telegramCandidatePrepared },
      { status: 202, ...DYNAMIC_RESPONSE },
    );
  } catch (error) {
    return Response.json({ error: error instanceof Error ? error.message : "Invalid payload" }, { status: 400 });
  }
}

function validateResult(value: unknown): ProductWorkerResult {
  if (!value || typeof value !== "object") throw new Error("Payload must be an object");
  const item = value as Record<string, unknown>;
  const status = text(item.status, "status", 20);
  if (!["completed", "needs_input", "blocked"].includes(status)) throw new Error("status is invalid");
  const missing = Array.isArray(item.missingFields) ? item.missingFields.map((entry) => text(entry, "missingFields", 80)) : [];
  if (missing.length > 10) throw new Error("missingFields is too large");
  return {
    requestId: text(item.requestId, "requestId", 80),
    status: status as ProductWorkerResult["status"],
    title: text(item.title, "title", 180),
    imageUrl: optionalHttps(item.imageUrl),
    currentPrice: status === "blocked" ? nonNegativeMoney(item.currentPrice, "currentPrice") : positiveMoney(item.currentPrice, "currentPrice"),
    oldPrice: item.oldPrice == null ? null : positiveMoney(item.oldPrice, "oldPrice"),
    analysisSummary: text(item.analysisSummary, "analysisSummary", 600),
    missingFields: missing,
    score: integer(item.score, "score"),
    confidence: integer(item.confidence, "confidence"),
    risk: text(item.risk, "risk", 500),
    nextAction: text(item.nextAction, "nextAction", 300),
    promiseReview: optionalText(item.promiseReview, "promiseReview", 500),
    creativeRecommendation: optionalText(item.creativeRecommendation, "creativeRecommendation", 500),
    commissionNotes: optionalText(item.commissionNotes, "commissionNotes", 500),
    funnelSuggestion: optionalText(item.funnelSuggestion, "funnelSuggestion", 500),
    affiliateReadiness: optionalText(item.affiliateReadiness, "affiliateReadiness", 300),
    affiliateLinkVerified: boolean(item.affiliateLinkVerified, "affiliateLinkVerified"),
    officialImageVerified: boolean(item.officialImageVerified, "officialImageVerified"),
    availabilityState: availability(item.availabilityState),
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

function integer(value: unknown, name: string) {
  if (!Number.isInteger(value) || (value as number) < 0 || (value as number) > 100) throw new Error(`${name} is invalid`);
  return value as number;
}

function positiveMoney(value: unknown, name: string) {
  if (typeof value !== "number" || !Number.isFinite(value) || value <= 0 || value > 10_000_000) {
    throw new Error(`${name} is invalid`);
  }
  return value;
}

function nonNegativeMoney(value: unknown, name: string) {
  if (typeof value !== "number" || !Number.isFinite(value) || value < 0 || value > 10_000_000) {
    throw new Error(`${name} is invalid`);
  }
  return value;
}

function boolean(value: unknown, name: string) {
  if (typeof value !== "boolean") throw new Error(`${name} is invalid`);
  return value;
}

function availability(value: unknown): ProductWorkerResult["availabilityState"] {
  if (!["in_stock", "out_of_stock", "unknown"].includes(String(value))) throw new Error("availabilityState is invalid");
  return value as ProductWorkerResult["availabilityState"];
}

function optionalHttps(value: unknown) {
  if (value == null || value === "") return "";
  const url = new URL(text(value, "imageUrl", 1_500));
  if (url.protocol !== "https:" || url.username || url.password) throw new Error("imageUrl must be public HTTPS");
  return url.toString();
}

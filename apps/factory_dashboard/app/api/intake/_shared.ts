import { type OpportunityIntake, upsertOpportunity } from "../dashboard/store";

const MAX_BODY_BYTES = 32_000;

export async function authenticatedOpportunityIntake(request: Request, label: string) {
  const unauthorized = await requireDashboardIntake(request, label);
  if (unauthorized) return unauthorized;
  const rawBody = await request.text();
  if (new TextEncoder().encode(rawBody).byteLength > MAX_BODY_BYTES) {
    return Response.json({ error: "Payload too large" }, { status: 413 });
  }
  try {
    const input = validateIntake(JSON.parse(rawBody) as unknown);
    return Response.json({ accepted: true, state: await upsertOpportunity(input) }, { status: 202 });
  } catch (error) {
    return Response.json({ error: error instanceof Error ? error.message : "Invalid payload" }, { status: 400 });
  }
}

export async function requireDashboardIntake(request: Request, label: string): Promise<Response | null> {
  const { env } = await import("cloudflare:workers");
  const expectedToken = (env as unknown as { DASHBOARD_INTAKE_TOKEN?: string }).DASHBOARD_INTAKE_TOKEN;
  if (!expectedToken) {
    return Response.json({ error: `${label} intake is not configured` }, { status: 503 });
  }
  const suppliedToken = request.headers.get("authorization")?.replace(/^Bearer\s+/i, "") ?? "";
  if (!constantTimeEqual(suppliedToken, expectedToken)) {
    return Response.json({ error: "Unauthorized" }, { status: 401 });
  }
  return null;
}

function validateIntake(value: unknown): OpportunityIntake {
  if (!value || typeof value !== "object") throw new Error("Payload must be an object");
  const item = value as Record<string, unknown>;
  const id = requiredString(item.id, "id", 100);
  if (!/^[a-z0-9][a-z0-9-]*$/.test(id)) throw new Error("id must be a lowercase slug");
  const priority = requiredString(item.priority, "priority", 10);
  if (!( ["low", "medium", "high"] as const).includes(priority as "low" | "medium" | "high")) {
    throw new Error("priority is invalid");
  }
  const sources = Array.isArray(item.sources) ? item.sources : [];
  if (sources.length < 1 || sources.length > 8) throw new Error("sources must contain 1 to 8 items");
  return {
    id,
    title: requiredString(item.title, "title", 180),
    source: requiredString(item.source, "source", 80),
    channel: requiredString(item.channel, "channel", 80),
    category: requiredString(item.category, "category", 40),
    summary: requiredString(item.summary, "summary", 600),
    priority: priority as OpportunityIntake["priority"],
    score: boundedInteger(item.score, "score"),
    confidence: boundedInteger(item.confidence, "confidence"),
    risk: requiredString(item.risk, "risk", 500),
    nextAction: requiredString(item.nextAction, "nextAction", 300),
    updatedAt: isoDate(item.updatedAt, "updatedAt"),
    sources: sources.map((source, index) => validateSource(source, id, index)),
  };
}

function validateSource(value: unknown, opportunityId: string, index: number): OpportunityIntake["sources"][number] {
  if (!value || typeof value !== "object") throw new Error(`sources[${index}] must be an object`);
  const source = value as Record<string, unknown>;
  const sourceType = requiredString(source.sourceType, `sources[${index}].sourceType`, 20);
  if (!( ["official", "reporting", "marketplace", "signal"] as const).includes(sourceType as OpportunityIntake["sources"][number]["sourceType"])) {
    throw new Error(`sources[${index}].sourceType is invalid`);
  }
  const url = requiredString(source.url, `sources[${index}].url`, 600);
  const parsed = new URL(url);
  if (parsed.protocol !== "https:" || parsed.username || parsed.password) throw new Error(`sources[${index}].url must be public HTTPS`);
  return {
    id: `${opportunityId}-source-${index + 1}`,
    label: requiredString(source.label, `sources[${index}].label`, 160),
    url: parsed.toString(),
    sourceType: sourceType as OpportunityIntake["sources"][number]["sourceType"],
    publishedAt: source.publishedAt == null ? null : isoDate(source.publishedAt, `sources[${index}].publishedAt`),
  };
}

function requiredString(value: unknown, name: string, maxLength: number) {
  if (typeof value !== "string" || !value.trim() || value.length > maxLength) throw new Error(`${name} is invalid`);
  return value.trim();
}

function boundedInteger(value: unknown, name: string) {
  if (!Number.isInteger(value) || (value as number) < 0 || (value as number) > 100) throw new Error(`${name} must be an integer from 0 to 100`);
  return value as number;
}

function isoDate(value: unknown, name: string) {
  const text = requiredString(value, name, 40);
  if (Number.isNaN(Date.parse(text))) throw new Error(`${name} must be an ISO date`);
  return new Date(text).toISOString();
}

function constantTimeEqual(left: string, right: string) {
  const length = Math.max(left.length, right.length);
  let difference = left.length ^ right.length;
  for (let index = 0; index < length; index += 1) {
    difference |= (left.charCodeAt(index) || 0) ^ (right.charCodeAt(index) || 0);
  }
  return difference === 0;
}

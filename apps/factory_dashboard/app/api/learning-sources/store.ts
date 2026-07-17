import { desc, eq } from "drizzle-orm";
import { createHash } from "node:crypto";
import { getDb } from "../../../db";
import { learningSourceRequests } from "../../../db/schema";

export type LearningSourceInput = {
  sourceUrl: string;
  canonicalUrl: string;
  externalId: string;
  title: string;
  ownerNotes: string;
  language: string;
  transcript: string;
};

export type LearningAuditInput = {
  sourceId: string;
  claimText: string;
  evidenceExcerpt: string;
  evidenceLocator: string;
  candidateStatement: string;
  applicability: string;
  risks: string;
};

export async function upsertLearningSource(input: LearningSourceInput) {
  await ensureLearningSchema();
  const db = getDb();
  const existing = await db.select().from(learningSourceRequests)
    .where(eq(learningSourceRequests.externalId, input.externalId)).limit(1);
  const current = existing[0];
  const transcript = input.transcript || current?.transcript || "";
  const transcriptAttached = transcript.length >= 200;
  const transcriptHash = transcriptAttached
    ? createHash("sha256").update(transcript).digest("hex")
    : "";
  const auditStillApplies = Boolean(
    current
    && current.transcriptHash
    && current.transcriptHash === transcriptHash
    && current.auditPacket !== "{}"
    && current.auditStatus !== "pending",
  );
  const now = new Date().toISOString();
  const values = {
    id: current?.id ?? crypto.randomUUID(),
    sourceUrl: input.sourceUrl,
    canonicalUrl: input.canonicalUrl,
    externalId: input.externalId,
    platform: "youtube",
    title: input.title || current?.title || `Vídeo do YouTube · ${input.externalId}`,
    ownerNotes: input.ownerNotes || current?.ownerNotes || "",
    language: input.language,
    status: auditStillApplies ? current.status : transcriptAttached ? "ready_for_audit" : "transcription_pending",
    transcriptStatus: transcriptAttached ? "attached" : "pending",
    transcript,
    transcriptHash,
    evidenceStatus: auditStillApplies ? current.evidenceStatus : "pending",
    auditStatus: auditStillApplies ? current.auditStatus : "pending",
    experimentStatus: "not_started",
    knowledgeStatus: auditStillApplies ? current.knowledgeStatus : "blocked",
    providerStatus: "not_called",
    publicationStatus: "blocked",
    estimatedCostUsdCents: 0,
    missingRequirements: auditStillApplies
      ? current.missingRequirements
      : JSON.stringify(missingRequirements(transcriptAttached)),
    auditPacket: auditStillApplies ? current.auditPacket : "{}",
    auditSubmittedAt: auditStillApplies ? current.auditSubmittedAt : "",
    submittedAt: current?.submittedAt ?? now,
    updatedAt: now,
  };
  await db.insert(learningSourceRequests).values(values).onConflictDoUpdate({
    target: learningSourceRequests.id,
    set: values,
  });
  return learningSourceState();
}

export async function auditLearningSource(input: LearningAuditInput) {
  await ensureLearningSchema();
  const db = getDb();
  const rows = await db.select().from(learningSourceRequests)
    .where(eq(learningSourceRequests.id, input.sourceId)).limit(1);
  const source = rows[0];
  if (!source) throw new Error("Fonte não encontrada");
  if (source.transcriptStatus !== "attached" || source.transcript.length < 200) {
    throw new Error("Anexe uma transcrição verificável antes da auditoria");
  }
  const transcriptHash = createHash("sha256").update(source.transcript).digest("hex");
  if (transcriptHash !== source.transcriptHash) {
    throw new Error("A transcrição mudou depois do registro; envie novamente antes de auditar");
  }
  const excerpt = input.evidenceExcerpt.trim();
  if (excerpt.length < 40 || !source.transcript.includes(excerpt)) {
    throw new Error("O trecho de evidência deve ter ao menos 40 caracteres e existir exatamente na transcrição");
  }
  const now = new Date().toISOString();
  const evidenceHash = createHash("sha256").update(excerpt).digest("hex");
  const sourceHash = createHash("sha256")
    .update(JSON.stringify({
      source_uri: source.canonicalUrl,
      transcript_sha256: source.transcriptHash,
    })).digest("hex");
  const claimHash = createHash("sha256")
    .update(JSON.stringify({
      claim_text: input.claimText,
      evidence_id: `evidence-transcript-${evidenceHash.slice(0, 16)}`,
      source_id: `source-${sourceHash.slice(0, 16)}`,
    })).digest("hex");
  const packet = {
    schemaVersion: "1.0",
    source: {
      sourceId: `source-${sourceHash.slice(0, 16)}`,
      sourceUri: source.canonicalUrl,
      transcriptSha256: source.transcriptHash,
      title: source.title,
    },
    evidence: {
      evidenceId: `evidence-transcript-${evidenceHash.slice(0, 16)}`,
      kind: "transcript",
      excerpt,
      locator: input.evidenceLocator,
      contentSha256: evidenceHash,
      independentSource: false,
    },
    claim: {
      claimId: `claim-${claimHash.slice(0, 16)}`,
      text: input.claimText,
    },
    audit: {
      auditId: `audit-${claimHash.slice(0, 16)}`,
      verdict: "partial",
      rationale: "O trecho confirma o que a fonte afirma, mas não prova de forma independente que a técnica funciona.",
      missingEvidence: ["Corroboração independente", "Experimento medido e aprovado"],
    },
    knowledgeDraft: {
      cardId: `knowledge-${claimHash.slice(0, 16)}`,
      statement: input.candidateStatement,
      applicability: input.applicability,
      risks: input.risks.split("\n").map((value) => value.trim()).filter(Boolean),
      status: "pending_audit",
    },
    safety: {
      providerCalled: false,
      providerCostUsd: 0,
      experimentStarted: false,
      memoryPromoted: false,
      publicationAttempted: false,
    },
    auditedAt: now,
  };
  await db.update(learningSourceRequests).set({
    status: "knowledge_candidate",
    evidenceStatus: "recorded",
    auditStatus: "partial",
    knowledgeStatus: "candidate",
    auditPacket: JSON.stringify(packet),
    auditSubmittedAt: now,
    missingRequirements: JSON.stringify([
      "Corroboração independente",
      "Experimento aprovado e medido",
      "Aprovação do owner para conhecimento oficial",
    ]),
    updatedAt: now,
  }).where(eq(learningSourceRequests.id, source.id));
  return learningSourceState();
}

export async function learningSourceState() {
  await ensureLearningSchema();
  const db = getDb();
  const items = await db.select().from(learningSourceRequests)
    .orderBy(desc(learningSourceRequests.updatedAt)).limit(50);
  return { items: items.map(publicItem) };
}

function missingRequirements(transcriptAttached: boolean) {
  return [
    ...(!transcriptAttached ? ["Transcrição verificável"] : []),
    "Evidências visuais ou trechos conferidos",
    "Alegações auditadas",
    "Experimento aprovado",
    "Aprovação do owner para conhecimento oficial",
  ];
}

function publicItem(item: typeof learningSourceRequests.$inferSelect) {
  return {
    id: item.id,
    sourceUrl: item.sourceUrl,
    canonicalUrl: item.canonicalUrl,
    externalId: item.externalId,
    platform: "youtube" as const,
    title: item.title,
    ownerNotes: item.ownerNotes,
    language: item.language,
    status: item.status,
    transcriptStatus: item.transcriptStatus,
    transcriptCharacters: item.transcript.length,
    thumbnailUrl: `https://i.ytimg.com/vi/${item.externalId}/hqdefault.jpg`,
    evidenceStatus: item.evidenceStatus,
    auditStatus: item.auditStatus,
    experimentStatus: item.experimentStatus,
    knowledgeStatus: item.knowledgeStatus,
    providerStatus: item.providerStatus,
    publicationStatus: item.publicationStatus,
    estimatedCostUsd: item.estimatedCostUsdCents / 100,
    missingRequirements: parseRequirements(item.missingRequirements),
    auditPacket: parseAuditPacket(item.auditPacket),
    auditSubmittedAt: item.auditSubmittedAt,
    submittedAt: item.submittedAt,
    updatedAt: item.updatedAt,
  };
}

function parseAuditPacket(value: string) {
  try {
    const parsed = JSON.parse(value) as Record<string, unknown>;
    return Object.keys(parsed).length ? parsed : null;
  } catch {
    return null;
  }
}

function parseRequirements(value: string) {
  try { return JSON.parse(value) as string[]; } catch { return []; }
}

async function ensureLearningSchema() {
  const { env } = await import("cloudflare:workers");
  await env.DB.prepare("CREATE TABLE IF NOT EXISTS learning_source_requests (id TEXT PRIMARY KEY, source_url TEXT NOT NULL UNIQUE, canonical_url TEXT NOT NULL UNIQUE, external_id TEXT NOT NULL UNIQUE, platform TEXT NOT NULL, title TEXT NOT NULL, owner_notes TEXT NOT NULL, language TEXT NOT NULL, status TEXT NOT NULL, transcript_status TEXT NOT NULL, transcript TEXT NOT NULL, transcript_hash TEXT NOT NULL, evidence_status TEXT NOT NULL, audit_status TEXT NOT NULL, experiment_status TEXT NOT NULL, knowledge_status TEXT NOT NULL, provider_status TEXT NOT NULL, publication_status TEXT NOT NULL, estimated_cost_usd_cents INTEGER NOT NULL, missing_requirements TEXT NOT NULL, audit_packet TEXT NOT NULL DEFAULT '{}', audit_submitted_at TEXT NOT NULL DEFAULT '', submitted_at TEXT NOT NULL, updated_at TEXT NOT NULL)").run();
  const columns = await env.DB.prepare("PRAGMA table_info(learning_source_requests)").all<{ name: string }>();
  const names = new Set((columns.results ?? []).map((column) => column.name));
  if (!names.has("audit_packet")) await env.DB.prepare("ALTER TABLE learning_source_requests ADD COLUMN audit_packet TEXT NOT NULL DEFAULT '{}'").run();
  if (!names.has("audit_submitted_at")) await env.DB.prepare("ALTER TABLE learning_source_requests ADD COLUMN audit_submitted_at TEXT NOT NULL DEFAULT ''").run();
  await env.DB.prepare("CREATE INDEX IF NOT EXISTS learning_source_status_idx ON learning_source_requests(status)").run();
}

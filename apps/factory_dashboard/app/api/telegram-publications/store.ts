import { asc, eq } from "drizzle-orm";
import { getDb } from "../../../db";
import {
  productIntakeRequests,
  telegramAutopilotPolicies,
  telegramPublicationRequests,
} from "../../../db/schema";

const DEFAULT_CHAT_ID = "@achadosbaratosBrasil";
const AUTOPILOT_POLICY_ID = "telegram-continuous-v1";
const AUTOPILOT_CONFIRMATION = "ATIVAR AUTOPILOTO TELEGRAM";
const AUTOPILOT_PAUSE_CONFIRMATION = "PAUSAR AUTOPILOTO TELEGRAM";
const AUTOPILOT_DAILY_LIMIT = 48;
const AUTOPILOT_INTERVAL_MINUTES = 30;
const ACTIVE_STATUSES = ["pending_approval", "queued", "publishing", "sent"];
const EDITORIAL_PRODUCT_ID = "editorial-welcome-achados-baratos-v1";
const EDITORIAL_MESSAGE = "Olá! Este é o canal Achados Baratos Brasil.\n\nAqui você encontrará uma curadoria de ofertas conferidas antes da publicação. Preços e disponibilidade serão informados em cada postagem e podem mudar.\n\nAcompanhe o canal para receber as próximas seleções.";

type CampaignPackage = { copy: string; missingToPublish: string[]; generatedAt: string };
type CandidateMetadata = {
  internalTitle: string;
  objective: string;
  audience: string;
  callToAction: string;
  origin: string;
  marketplace: string;
  risks: string[];
  validUntil: string;
  idempotencyKey: string;
  publicationMode: string;
  isAffiliate: boolean;
};

type ClaimedTelegramPublication = {
  id: string;
  product_id: string;
  chat_id: string;
  message_text: string;
  affiliate_url: string;
  image_url: string;
  link_preview_enabled: number;
  owner_approved: number;
  approved_at: string;
  authorization_kind: string;
  policy_id: string;
  policy_version: number;
  lease_token: string;
  lease_expires_at: string;
};

const MAX_PACKAGE_AGE_MS = 2 * 60 * 60 * 1000;
const MAX_PHOTO_CAPTION_LENGTH = 1024;
const LEASE_DURATION_MS = 5 * 60 * 1000;

const ATOMIC_TELEGRAM_CLAIM_SQL = `
UPDATE telegram_publication_requests
SET status = 'publishing', claimed_at = ?, lease_token = ?, lease_expires_at = ?, updated_at = ?
WHERE id = (
  SELECT id
  FROM telegram_publication_requests
  WHERE status = 'queued'
    AND owner_approved = 1
    AND approved_at >= ?
    AND approved_at <= ?
    AND json_extract(
      CASE WHEN json_valid(candidate_metadata) THEN candidate_metadata ELSE '{}' END,
      '$.validUntil'
    ) >= ?
  ORDER BY created_at ASC, id ASC
  LIMIT 1
)
  AND status = 'queued'
RETURNING id, product_id, chat_id, message_text, affiliate_url, image_url,
  link_preview_enabled, owner_approved, approved_at, authorization_kind,
  policy_id, policy_version, lease_token, lease_expires_at
`;

export async function telegramPublicationState() {
  await ensureTelegramPublicationSchema();
  const db = getDb();
  const rows = await db.select().from(telegramPublicationRequests)
    .orderBy(asc(telegramPublicationRequests.createdAt)).limit(100);
  const policies = await db.select().from(telegramAutopilotPolicies)
    .where(eq(telegramAutopilotPolicies.id, AUTOPILOT_POLICY_ID)).limit(1);
  return {
    publications: rows.map(publicPublication),
    autopilot: policies[0] ? publicPolicy(policies[0]) : defaultPolicyState(),
  };
}

export async function activateTelegramAutopilot(confirmation: string) {
  if (confirmation !== AUTOPILOT_CONFIRMATION) throw new Error("A ativação contínua exige confirmação explícita");
  await ensureTelegramPublicationSchema();
  const { env } = await import("cloudflare:workers");
  const now = new Date().toISOString();
  const dayKey = saoPauloDayKey();
  await env.DB.prepare(`
    INSERT INTO telegram_autopilot_policies (
      id, status, version, chat_id, max_publications_per_day, sent_today,
      failed_today, reserved_today, day_key, min_interval_minutes, next_run_at,
      last_reserved_at, last_sent_at, allowed_marketplaces, owner_confirmation,
      created_at, updated_at
    ) VALUES (?, 'active', 1, ?, ?, 0, 0, 0, ?, ?, ?, '', '', ?, ?, ?, ?)
    ON CONFLICT(id) DO UPDATE SET
      status = 'active', version = telegram_autopilot_policies.version + 1,
      chat_id = excluded.chat_id, max_publications_per_day = excluded.max_publications_per_day,
      min_interval_minutes = excluded.min_interval_minutes,
      allowed_marketplaces = excluded.allowed_marketplaces,
      owner_confirmation = excluded.owner_confirmation, next_run_at = excluded.next_run_at,
      updated_at = excluded.updated_at,
      sent_today = CASE WHEN telegram_autopilot_policies.day_key = excluded.day_key THEN telegram_autopilot_policies.sent_today ELSE 0 END,
      failed_today = CASE WHEN telegram_autopilot_policies.day_key = excluded.day_key THEN telegram_autopilot_policies.failed_today ELSE 0 END,
      reserved_today = CASE WHEN telegram_autopilot_policies.day_key = excluded.day_key THEN telegram_autopilot_policies.reserved_today ELSE 0 END,
      day_key = excluded.day_key
  `).bind(
    AUTOPILOT_POLICY_ID, DEFAULT_CHAT_ID, AUTOPILOT_DAILY_LIMIT, dayKey,
    AUTOPILOT_INTERVAL_MINUTES, now, JSON.stringify(["Mercado Livre"]),
    confirmation, now, now,
  ).run();
  return telegramPublicationState();
}

export async function pauseTelegramAutopilot(confirmation: string) {
  if (confirmation !== AUTOPILOT_PAUSE_CONFIRMATION) throw new Error("A pausa exige confirmação explícita");
  await ensureTelegramPublicationSchema();
  const { env } = await import("cloudflare:workers");
  await env.DB.prepare(`
    UPDATE telegram_autopilot_policies
    SET status = 'paused', version = version + 1, owner_confirmation = ?, updated_at = ?
    WHERE id = ?
  `).bind(confirmation, new Date().toISOString(), AUTOPILOT_POLICY_ID).run();
  return telegramPublicationState();
}

export async function queueTelegramPublication(productId: string) {
  await ensureTelegramPublicationSchema();
  const db = getDb();
  const [product] = await db.select().from(productIntakeRequests)
    .where(eq(productIntakeRequests.id, productId)).limit(1);
  if (!product) throw new Error("Produto não encontrado");
  if (product.targetChannel !== "telegram_public") throw new Error("Este pacote não está destinado ao Telegram público");
  if (!product.affiliateUrl) throw new Error("Confirme o link afiliado antes de preparar o candidato");
  if (!product.currentPriceCents) throw new Error("Confirme o preço atual antes de preparar o candidato");
  if (!product.commissionConfirmed) throw new Error("Confirme que o link veio do programa oficial de afiliados");
  if (!product.channelRegistered) throw new Error("Confirme o cadastro do canal público no programa de afiliados");
  if (!product.creativeReviewStatus) throw new Error("Conclua a revisão visual antes de preparar o candidato");

  let campaignPackage: CampaignPackage;
  try { campaignPackage = JSON.parse(product.campaignPackage || "") as CampaignPackage; }
  catch { throw new Error("Prepare novamente o pacote antes de criar o candidato"); }
  const blockers = (campaignPackage.missingToPublish ?? []).filter((field) => field !== "aprovação final do owner");
  if (blockers.length) throw new Error(`Resolva antes de preparar: ${blockers.join(", ")}`);
  const generatedAt = Date.parse(campaignPackage.generatedAt ?? "");
  const packageAge = Date.now() - generatedAt;
  if (!Number.isFinite(generatedAt) || packageAge < -5 * 60 * 1000 || packageAge > MAX_PACKAGE_AGE_MS) {
    throw new Error("Preço e pacote estão antigos. Confirme os dados comerciais novamente");
  }
  const imageUrl = publicHttpsImageUrl(product.imageUrl) ? product.imageUrl : "";
  const message = String(campaignPackage.copy ?? "").trim();
  const maxLength = imageUrl ? MAX_PHOTO_CAPTION_LENGTH : 4096;
  if (!message || message.length > maxLength || !message.includes(product.affiliateUrl) || !message.includes("#publi")) {
    throw new Error("A prévia do Telegram está inválida ou não contém o link afiliado confirmado");
  }
  const metadata: CandidateMetadata = {
    internalTitle: product.productName || "Oferta para revisão",
    objective: "Apresentar uma oferta verificada ao público do canal.",
    audience: "Pessoas interessadas em ofertas e economia nas compras.",
    callToAction: "Conferir a oferta no link informado.",
    origin: "Pacote comercial preparado pela AI Content Factory a partir de dados confirmados pelo owner.",
    marketplace: product.marketplace,
    risks: ["Preço e disponibilidade podem mudar", "O link e os dados comerciais devem permanecer válidos"],
    validUntil: new Date(generatedAt + MAX_PACKAGE_AGE_MS).toISOString(),
    idempotencyKey: `telegram-product-${productId}-${simpleHash(message)}`,
    publicationMode: "REAL CONTROLADO - MANUAL OU POLITICA DELEGADA",
    isAffiliate: true,
  };
  return insertPendingCandidate({
    productId, message, affiliateUrl: product.affiliateUrl, imageUrl, metadata,
    validationSnapshotHash: simpleHash(JSON.stringify({
      marketplace: product.marketplace,
      price: product.currentPriceCents,
      commissionConfirmed: product.commissionConfirmed,
      channelRegistered: product.channelRegistered,
      creativeReviewStatus: product.creativeReviewStatus,
      generatedAt: campaignPackage.generatedAt,
    })),
  });
}

export async function prepareEditorialTelegramCandidate() {
  const validUntil = new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString();
  const metadata: CandidateMetadata = {
    internalTitle: "Boas-vindas ao canal Achados Baratos Brasil",
    objective: "Apresentar o propósito editorial do canal antes das primeiras ofertas.",
    audience: "Pessoas interessadas em ofertas selecionadas e economia nas compras.",
    callToAction: "Acompanhar o canal para receber as próximas seleções.",
    origin: "Conteúdo editorial original da AI Content Factory.",
    marketplace: "",
    risks: ["Não prometer preço ou disponibilidade permanentes", "Não confundir a mensagem editorial com uma oferta comercial"],
    validUntil,
    idempotencyKey: `telegram-editorial-${EDITORIAL_PRODUCT_ID}-${simpleHash(EDITORIAL_MESSAGE)}`,
    publicationMode: "REAL CONTROLADO - APROVACAO MANUAL",
    isAffiliate: false,
  };
  return insertPendingCandidate({
    productId: EDITORIAL_PRODUCT_ID,
    message: EDITORIAL_MESSAGE,
    affiliateUrl: "",
    imageUrl: "",
    metadata,
    validationSnapshotHash: simpleHash(`editorial:${EDITORIAL_MESSAGE}`),
  });
}

async function insertPendingCandidate(input: {
  productId: string;
  message: string;
  affiliateUrl: string;
  imageUrl: string;
  metadata: CandidateMetadata;
  validationSnapshotHash: string;
}) {
  await ensureTelegramPublicationSchema();
  const db = getDb();
  const existing = await db.select().from(telegramPublicationRequests)
    .where(eq(telegramPublicationRequests.productId, input.productId));
  if (existing.some((row) => ACTIVE_STATUSES.includes(row.status))) return telegramPublicationState();
  if (input.affiliateUrl) {
    const sameLink = await db.select().from(telegramPublicationRequests)
      .where(eq(telegramPublicationRequests.affiliateUrl, input.affiliateUrl));
    if (sameLink.some((row) => row.status === "sent")) throw new Error("Este link afiliado já foi publicado no Telegram");
  }
  const now = new Date().toISOString();
  await db.insert(telegramPublicationRequests).values({
    id: crypto.randomUUID(), productId: input.productId, status: "pending_approval",
    chatId: DEFAULT_CHAT_ID, messageText: input.message, affiliateUrl: input.affiliateUrl,
    imageUrl: input.imageUrl, ownerApproved: 0, linkPreviewEnabled: 1,
    telegramMessageId: null, error: "", approvedAt: "", claimedAt: null, sentAt: null,
    candidateMetadata: JSON.stringify(input.metadata), authorizationKind: "manual",
    policyId: "", policyVersion: 0, idempotencyKey: input.metadata.idempotencyKey,
    contentHash: simpleHash(input.message), validationSnapshotHash: input.validationSnapshotHash,
    leaseToken: "", leaseExpiresAt: "", createdAt: now, updatedAt: now,
  });
  return telegramPublicationState();
}

export async function approveTelegramPublication(requestId: string) {
  await ensureTelegramPublicationSchema();
  const db = getDb();
  const [item] = await db.select().from(telegramPublicationRequests)
    .where(eq(telegramPublicationRequests.id, requestId)).limit(1);
  if (!item || item.status !== "pending_approval") throw new Error("Somente candidatos pendentes podem ser aprovados");
  const metadata = parseMetadata(item.candidateMetadata);
  if (!metadata.validUntil || Date.parse(metadata.validUntil) < Date.now()) throw new Error("O candidato expirou e precisa ser preparado novamente");
  const now = new Date().toISOString();
  await db.update(telegramPublicationRequests).set({
    status: "queued", ownerApproved: 1, approvedAt: now, error: "", claimedAt: null,
    authorizationKind: "manual", policyId: "", policyVersion: 0,
    leaseToken: "", leaseExpiresAt: "", updatedAt: now,
  }).where(eq(telegramPublicationRequests.id, requestId));
  return telegramPublicationState();
}

export async function claimTelegramPublication() {
  await ensureTelegramPublicationSchema();
  const existing = await claimNextQueuedPublication();
  if (existing.items.length) return existing;
  await delegateOneAutopilotCandidate();
  return claimNextQueuedPublication();
}

async function claimNextQueuedPublication() {
  const { env } = await import("cloudflare:workers");
  const now = new Date().toISOString();
  const leaseToken = crypto.randomUUID();
  const leaseExpiresAt = new Date(Date.now() + LEASE_DURATION_MS).toISOString();
  const earliestApproval = new Date(Date.now() - MAX_PACKAGE_AGE_MS).toISOString();
  const latestApproval = new Date(Date.now() + 5 * 60 * 1000).toISOString();
  const result = await env.DB.prepare(ATOMIC_TELEGRAM_CLAIM_SQL)
    .bind(now, leaseToken, leaseExpiresAt, now, earliestApproval, latestApproval, now)
    .all<ClaimedTelegramPublication>();
  const item = result.results[0];
  if (!item) return { items: [] };
  return { items: [{
    id: item.id, productId: item.product_id, chatId: item.chat_id, messageText: item.message_text,
    affiliateUrl: item.affiliate_url, imageUrl: item.image_url,
    linkPreviewEnabled: Boolean(item.link_preview_enabled), ownerApproved: Boolean(item.owner_approved),
    approvedAt: item.approved_at, authorizationKind: item.authorization_kind,
    policyId: item.policy_id, policyVersion: item.policy_version,
    leaseToken: item.lease_token, leaseExpiresAt: item.lease_expires_at,
  }] };
}

async function delegateOneAutopilotCandidate() {
  const { env } = await import("cloudflare:workers");
  const now = new Date();
  const nowIso = now.toISOString();
  const dayKey = saoPauloDayKey(now);
  await env.DB.prepare(`
    UPDATE telegram_autopilot_policies
    SET sent_today = 0, failed_today = 0, reserved_today = 0,
        day_key = ?, next_run_at = ?, updated_at = ?
    WHERE id = ? AND day_key <> ?
  `).bind(dayKey, nowIso, nowIso, AUTOPILOT_POLICY_ID, dayKey).run();

  const nextRunAt = new Date(now.getTime() + AUTOPILOT_INTERVAL_MINUTES * 60 * 1000).toISOString();
  const reservation = await env.DB.prepare(`
    UPDATE telegram_autopilot_policies
    SET reserved_today = reserved_today + 1, next_run_at = ?, last_reserved_at = ?, updated_at = ?
    WHERE id = ? AND status = 'active' AND chat_id = ?
      AND reserved_today < max_publications_per_day
      AND (next_run_at = '' OR next_run_at <= ?)
    RETURNING version
  `).bind(nextRunAt, nowIso, nowIso, AUTOPILOT_POLICY_ID, DEFAULT_CHAT_ID, nowIso)
    .all<{ version: number }>();
  const policy = reservation.results[0];
  if (!policy) return;

  const delegated = await env.DB.prepare(`
    UPDATE telegram_publication_requests
    SET status = 'queued', owner_approved = 1, approved_at = ?,
        authorization_kind = 'autopilot_policy', policy_id = ?, policy_version = ?,
        error = '', claimed_at = NULL, lease_token = '', lease_expires_at = '', updated_at = ?
    WHERE id = (
      SELECT id FROM telegram_publication_requests
      WHERE status = 'pending_approval' AND chat_id = ? AND affiliate_url <> ''
        AND idempotency_key <> '' AND content_hash <> '' AND validation_snapshot_hash <> ''
        AND json_extract(CASE WHEN json_valid(candidate_metadata) THEN candidate_metadata ELSE '{}' END, '$.isAffiliate') = 1
        AND json_extract(CASE WHEN json_valid(candidate_metadata) THEN candidate_metadata ELSE '{}' END, '$.marketplace') = 'Mercado Livre'
        AND json_extract(CASE WHEN json_valid(candidate_metadata) THEN candidate_metadata ELSE '{}' END, '$.validUntil') >= ?
      ORDER BY created_at ASC, id ASC LIMIT 1
    ) AND status = 'pending_approval'
    RETURNING id
  `).bind(nowIso, AUTOPILOT_POLICY_ID, policy.version, nowIso, DEFAULT_CHAT_ID, nowIso)
    .all<{ id: string }>();
  if (!delegated.results.length) {
    await env.DB.prepare(`
      UPDATE telegram_autopilot_policies
      SET reserved_today = CASE WHEN reserved_today > 0 THEN reserved_today - 1 ELSE 0 END, updated_at = ?
      WHERE id = ?
    `).bind(nowIso, AUTOPILOT_POLICY_ID).run();
  }
}

export async function applyTelegramPublicationResult(input: {
  requestId: string;
  leaseToken: string;
  status: "sent" | "failed";
  messageId: number | null;
  error: string;
}) {
  await ensureTelegramPublicationSchema();
  if (!input.leaseToken) throw new Error("Reserva do worker ausente");
  const { env } = await import("cloudflare:workers");
  const now = new Date().toISOString();
  const result = await env.DB.prepare(`
    UPDATE telegram_publication_requests
    SET status = ?, telegram_message_id = ?, error = ?, sent_at = ?,
        lease_token = '', lease_expires_at = '', updated_at = ?
    WHERE id = ? AND status = 'publishing' AND lease_token = ? AND lease_expires_at >= ?
    RETURNING authorization_kind, policy_id
  `).bind(
    input.status,
    input.status === "sent" ? input.messageId : null,
    input.status === "failed" ? input.error.slice(0, 500) : "",
    input.status === "sent" ? now : null,
    now, input.requestId, input.leaseToken, now,
  ).all<{ authorization_kind: string; policy_id: string }>();
  const item = result.results[0];
  if (!item) throw new Error("Reserva expirada, inválida ou já concluída");
  if (item.authorization_kind === "autopilot_policy" && item.policy_id) {
    const counter = input.status === "sent" ? "sent_today" : "failed_today";
    await env.DB.prepare(`
      UPDATE telegram_autopilot_policies
      SET ${counter} = ${counter} + 1,
          last_sent_at = CASE WHEN ? = 'sent' THEN ? ELSE last_sent_at END,
          updated_at = ?
      WHERE id = ?
    `).bind(input.status, now, now, item.policy_id).run();
  }
  return telegramPublicationState();
}

export async function retryTelegramPublication(requestId: string) {
  await ensureTelegramPublicationSchema();
  const db = getDb();
  const [item] = await db.select().from(telegramPublicationRequests)
    .where(eq(telegramPublicationRequests.id, requestId)).limit(1);
  if (!item || item.status !== "failed") throw new Error("Somente envios com falha podem voltar para revisão");
  await db.update(telegramPublicationRequests).set({
    status: "pending_approval", ownerApproved: 0, approvedAt: "", error: "", claimedAt: null,
    authorizationKind: "manual", policyId: "", policyVersion: 0,
    leaseToken: "", leaseExpiresAt: "", updatedAt: new Date().toISOString(),
  }).where(eq(telegramPublicationRequests.id, requestId));
  return telegramPublicationState();
}

async function ensureTelegramPublicationSchema() {
  const { env } = await import("cloudflare:workers");
  await env.DB.prepare(`CREATE TABLE IF NOT EXISTS telegram_publication_requests (
    id TEXT PRIMARY KEY, product_id TEXT NOT NULL, status TEXT NOT NULL, chat_id TEXT NOT NULL,
    message_text TEXT NOT NULL, affiliate_url TEXT NOT NULL, image_url TEXT NOT NULL,
    owner_approved INTEGER NOT NULL, link_preview_enabled INTEGER NOT NULL,
    telegram_message_id INTEGER, error TEXT NOT NULL, approved_at TEXT NOT NULL,
    claimed_at TEXT, sent_at TEXT, candidate_metadata TEXT NOT NULL DEFAULT '{}',
    authorization_kind TEXT NOT NULL DEFAULT 'manual', policy_id TEXT NOT NULL DEFAULT '',
    policy_version INTEGER NOT NULL DEFAULT 0, idempotency_key TEXT NOT NULL DEFAULT '',
    content_hash TEXT NOT NULL DEFAULT '', validation_snapshot_hash TEXT NOT NULL DEFAULT '',
    lease_token TEXT NOT NULL DEFAULT '', lease_expires_at TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL, updated_at TEXT NOT NULL
  )`).run();
  const additiveColumns = [
    "candidate_metadata TEXT NOT NULL DEFAULT '{}'",
    "authorization_kind TEXT NOT NULL DEFAULT 'manual'",
    "policy_id TEXT NOT NULL DEFAULT ''",
    "policy_version INTEGER NOT NULL DEFAULT 0",
    "idempotency_key TEXT NOT NULL DEFAULT ''",
    "content_hash TEXT NOT NULL DEFAULT ''",
    "validation_snapshot_hash TEXT NOT NULL DEFAULT ''",
    "lease_token TEXT NOT NULL DEFAULT ''",
    "lease_expires_at TEXT NOT NULL DEFAULT ''",
  ];
  for (const definition of additiveColumns) {
    try { await env.DB.prepare(`ALTER TABLE telegram_publication_requests ADD COLUMN ${definition}`).run(); }
    catch { /* The additive column already exists. */ }
  }
  await env.DB.prepare(`CREATE TABLE IF NOT EXISTS telegram_autopilot_policies (
    id TEXT PRIMARY KEY, status TEXT NOT NULL, version INTEGER NOT NULL, chat_id TEXT NOT NULL,
    max_publications_per_day INTEGER NOT NULL, sent_today INTEGER NOT NULL,
    failed_today INTEGER NOT NULL, reserved_today INTEGER NOT NULL, day_key TEXT NOT NULL,
    min_interval_minutes INTEGER NOT NULL, next_run_at TEXT NOT NULL,
    last_reserved_at TEXT NOT NULL, last_sent_at TEXT NOT NULL,
    allowed_marketplaces TEXT NOT NULL, owner_confirmation TEXT NOT NULL,
    created_at TEXT NOT NULL, updated_at TEXT NOT NULL
  )`).run();
  await env.DB.prepare("CREATE INDEX IF NOT EXISTS telegram_publication_status_idx ON telegram_publication_requests(status)").run();
  await env.DB.prepare("CREATE INDEX IF NOT EXISTS telegram_publication_product_idx ON telegram_publication_requests(product_id)").run();
  await env.DB.prepare("CREATE UNIQUE INDEX IF NOT EXISTS telegram_publication_idempotency_idx ON telegram_publication_requests(idempotency_key) WHERE idempotency_key <> ''").run();
}

function publicPublication(item: typeof telegramPublicationRequests.$inferSelect) {
  return {
    id: item.id, productId: item.productId, status: item.status, chatId: item.chatId,
    messageText: item.messageText, affiliateUrl: item.affiliateUrl, imageUrl: item.imageUrl,
    linkPreviewEnabled: Boolean(item.linkPreviewEnabled), telegramMessageId: item.telegramMessageId,
    error: item.error, approvedAt: item.approvedAt, sentAt: item.sentAt, updatedAt: item.updatedAt,
    authorizationKind: item.authorizationKind, policyId: item.policyId,
    candidate: parseMetadata(item.candidateMetadata),
  };
}

function publicPolicy(item: typeof telegramAutopilotPolicies.$inferSelect) {
  return {
    id: item.id, status: item.status, version: item.version, chatId: item.chatId,
    maxPublicationsPerDay: item.maxPublicationsPerDay, sentToday: item.sentToday,
    failedToday: item.failedToday, reservedToday: item.reservedToday,
    dayKey: item.dayKey, minIntervalMinutes: item.minIntervalMinutes,
    nextRunAt: item.nextRunAt, lastReservedAt: item.lastReservedAt,
    lastSentAt: item.lastSentAt, allowedMarketplaces: parseStringArray(item.allowedMarketplaces),
    continuous: true,
  };
}

function defaultPolicyState() {
  return {
    id: AUTOPILOT_POLICY_ID, status: "inactive", version: 0, chatId: DEFAULT_CHAT_ID,
    maxPublicationsPerDay: AUTOPILOT_DAILY_LIMIT, sentToday: 0, failedToday: 0,
    reservedToday: 0, dayKey: saoPauloDayKey(), minIntervalMinutes: AUTOPILOT_INTERVAL_MINUTES,
    nextRunAt: "", lastReservedAt: "", lastSentAt: "",
    allowedMarketplaces: ["Mercado Livre"], continuous: true,
  };
}

function parseMetadata(value: string): CandidateMetadata {
  try { return JSON.parse(value || "{}") as CandidateMetadata; }
  catch { return {} as CandidateMetadata; }
}

function parseStringArray(value: string) {
  try {
    const parsed = JSON.parse(value || "[]");
    return Array.isArray(parsed) ? parsed.map(String) : [];
  } catch { return []; }
}

function saoPauloDayKey(date = new Date()) {
  const parts = new Intl.DateTimeFormat("en-CA", {
    timeZone: "America/Sao_Paulo", year: "numeric", month: "2-digit", day: "2-digit",
  }).formatToParts(date);
  const values = Object.fromEntries(parts.map((part) => [part.type, part.value]));
  return `${values.year}-${values.month}-${values.day}`;
}

function simpleHash(value: string) {
  let hash = 2166136261;
  for (let index = 0; index < value.length; index += 1) hash = Math.imul(hash ^ value.charCodeAt(index), 16777619);
  return (hash >>> 0).toString(16).padStart(8, "0");
}

function publicHttpsImageUrl(value: string) {
  if (!value || value.length > 2048) return false;
  try {
    const url = new URL(value); const host = url.hostname.toLowerCase();
    if (url.protocol !== "https:" || url.username || url.password || !host) return false;
    if (host === "localhost" || host.endsWith(".localhost")) return false;
    if (/^(127\.|10\.|0\.|169\.254\.|192\.168\.)/.test(host)) return false;
    if (/^172\.(1[6-9]|2\d|3[01])\./.test(host)) return false;
    return true;
  } catch { return false; }
}

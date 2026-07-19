import { asc, eq } from "drizzle-orm";
import { getDb } from "../../../db";
import { productIntakeRequests, telegramPublicationRequests } from "../../../db/schema";

const DEFAULT_CHAT_ID = "@achadosbaratosBrasil";
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
  risks: string[];
  validUntil: string;
  idempotencyKey: string;
  publicationMode: string;
  isAffiliate: boolean;
};

const MAX_PACKAGE_AGE_MS = 2 * 60 * 60 * 1000;
const MAX_PHOTO_CAPTION_LENGTH = 1024;

const ATOMIC_TELEGRAM_CLAIM_SQL = `
UPDATE telegram_publication_requests
SET status = 'publishing', claimed_at = ?, updated_at = ?
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
  link_preview_enabled, owner_approved, approved_at
`;

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
};

export async function telegramPublicationState() {
  await ensureTelegramPublicationSchema();
  const rows = await getDb().select().from(telegramPublicationRequests)
    .orderBy(asc(telegramPublicationRequests.createdAt)).limit(100);
  return { publications: rows.map(publicPublication) };
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
    risks: ["Preço e disponibilidade podem mudar", "O link e os dados comerciais devem permanecer válidos"],
    validUntil: new Date(generatedAt + MAX_PACKAGE_AGE_MS).toISOString(),
    idempotencyKey: `telegram-product-${productId}-${simpleHash(message)}`,
    publicationMode: "REAL CONTROLADO - OPT-IN E APROVACAO",
    isAffiliate: true,
  };
  return insertPendingCandidate({ productId, message, affiliateUrl: product.affiliateUrl, imageUrl, metadata });
}

export async function prepareEditorialTelegramCandidate() {
  const validUntil = new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString();
  const metadata: CandidateMetadata = {
    internalTitle: "Boas-vindas ao canal Achados Baratos Brasil",
    objective: "Apresentar o propósito editorial do canal antes das primeiras ofertas.",
    audience: "Pessoas interessadas em ofertas selecionadas e economia nas compras.",
    callToAction: "Acompanhar o canal para receber as próximas seleções.",
    origin: "Conteúdo editorial original da AI Content Factory.",
    risks: ["Não prometer preço ou disponibilidade permanentes", "Não confundir a mensagem editorial com uma oferta comercial"],
    validUntil,
    idempotencyKey: `telegram-editorial-${EDITORIAL_PRODUCT_ID}-${simpleHash(EDITORIAL_MESSAGE)}`,
    publicationMode: "REAL CONTROLADO - OPT-IN E APROVACAO",
    isAffiliate: false,
  };
  return insertPendingCandidate({ productId: EDITORIAL_PRODUCT_ID, message: EDITORIAL_MESSAGE, affiliateUrl: "", imageUrl: "", metadata });
}

async function insertPendingCandidate(input: { productId: string; message: string; affiliateUrl: string; imageUrl: string; metadata: CandidateMetadata }) {
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
    candidateMetadata: JSON.stringify(input.metadata), createdAt: now, updatedAt: now,
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
    status: "queued", ownerApproved: 1, approvedAt: now, error: "", claimedAt: null, updatedAt: now,
  }).where(eq(telegramPublicationRequests.id, requestId));
  return telegramPublicationState();
}

export async function claimTelegramPublication() {
  await ensureTelegramPublicationSchema();
  const { env } = await import("cloudflare:workers");
  const now = new Date().toISOString();
  const earliestApproval = new Date(Date.now() - MAX_PACKAGE_AGE_MS).toISOString();
  const latestApproval = new Date(Date.now() + 5 * 60 * 1000).toISOString();
  const result = await env.DB.prepare(ATOMIC_TELEGRAM_CLAIM_SQL)
    .bind(now, now, earliestApproval, latestApproval, now)
    .all<ClaimedTelegramPublication>();
  const item = result.results[0];
  if (!item) return { items: [] };
  return { items: [{
    id: item.id, productId: item.product_id, chatId: item.chat_id, messageText: item.message_text,
    affiliateUrl: item.affiliate_url, imageUrl: item.image_url,
    linkPreviewEnabled: Boolean(item.link_preview_enabled), ownerApproved: Boolean(item.owner_approved), approvedAt: item.approved_at,
  }] };
}

export async function applyTelegramPublicationResult(input: { requestId: string; status: "sent" | "failed"; messageId: number | null; error: string }) {
  await ensureTelegramPublicationSchema();
  const db = getDb();
  const [item] = await db.select().from(telegramPublicationRequests)
    .where(eq(telegramPublicationRequests.id, input.requestId)).limit(1);
  if (!item || item.status !== "publishing") throw new Error("Solicitação não está reservada para publicação");
  const now = new Date().toISOString();
  await db.update(telegramPublicationRequests).set({
    status: input.status, telegramMessageId: input.status === "sent" ? input.messageId : null,
    error: input.status === "failed" ? input.error.slice(0, 500) : "", sentAt: input.status === "sent" ? now : null, updatedAt: now,
  }).where(eq(telegramPublicationRequests.id, input.requestId));
  return telegramPublicationState();
}

export async function retryTelegramPublication(requestId: string) {
  await ensureTelegramPublicationSchema();
  const db = getDb();
  const [item] = await db.select().from(telegramPublicationRequests)
    .where(eq(telegramPublicationRequests.id, requestId)).limit(1);
  if (!item || item.status !== "failed") throw new Error("Somente envios com falha podem voltar para revisão");
  await db.update(telegramPublicationRequests).set({
    status: "pending_approval", ownerApproved: 0, approvedAt: "", error: "", claimedAt: null, updatedAt: new Date().toISOString(),
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
    claimed_at TEXT, sent_at TEXT, candidate_metadata TEXT NOT NULL DEFAULT '{}', created_at TEXT NOT NULL, updated_at TEXT NOT NULL
  )`).run();
  try { await env.DB.prepare("ALTER TABLE telegram_publication_requests ADD COLUMN candidate_metadata TEXT NOT NULL DEFAULT '{}'").run(); }
  catch { /* Existing schema already has the additive column. */ }
  await env.DB.prepare("CREATE INDEX IF NOT EXISTS telegram_publication_status_idx ON telegram_publication_requests(status)").run();
  await env.DB.prepare("CREATE INDEX IF NOT EXISTS telegram_publication_product_idx ON telegram_publication_requests(product_id)").run();
}

function publicPublication(item: typeof telegramPublicationRequests.$inferSelect) {
  return {
    id: item.id, productId: item.productId, status: item.status, chatId: item.chatId,
    messageText: item.messageText, affiliateUrl: item.affiliateUrl, imageUrl: item.imageUrl,
    linkPreviewEnabled: Boolean(item.linkPreviewEnabled), telegramMessageId: item.telegramMessageId,
    error: item.error, approvedAt: item.approvedAt, sentAt: item.sentAt, updatedAt: item.updatedAt,
    candidate: parseMetadata(item.candidateMetadata),
  };
}

function parseMetadata(value: string): CandidateMetadata {
  try { return JSON.parse(value || "{}") as CandidateMetadata; }
  catch { return {} as CandidateMetadata; }
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

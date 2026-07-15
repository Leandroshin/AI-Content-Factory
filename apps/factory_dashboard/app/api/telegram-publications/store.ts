import { asc, eq } from "drizzle-orm";
import { getDb } from "../../../db";
import { productIntakeRequests, telegramPublicationRequests } from "../../../db/schema";

const DEFAULT_CHAT_ID = "@achadosbaratosBrasil";
const ACTIVE_STATUSES = ["queued", "publishing", "sent"];

type CampaignPackage = {
  copy: string;
  missingToPublish: string[];
};

export async function telegramPublicationState() {
  await ensureTelegramPublicationSchema();
  const db = getDb();
  const rows = await db.select().from(telegramPublicationRequests)
    .orderBy(asc(telegramPublicationRequests.createdAt)).limit(100);
  return { publications: rows.map(publicPublication) };
}

export async function queueTelegramPublication(productId: string) {
  await ensureTelegramPublicationSchema();
  const db = getDb();
  const products = await db.select().from(productIntakeRequests)
    .where(eq(productIntakeRequests.id, productId)).limit(1);
  const product = products[0];
  if (!product) throw new Error("Produto não encontrado");
  if (product.targetChannel !== "telegram_public") throw new Error("Este pacote não está destinado ao Telegram público");
  if (!product.affiliateUrl) throw new Error("Confirme o link afiliado antes de publicar");
  if (!product.currentPriceCents) throw new Error("Confirme o preço atual antes de publicar");
  if (!product.commissionConfirmed) throw new Error("Confirme que o link veio do programa oficial de afiliados");
  if (!product.channelRegistered) throw new Error("Confirme o cadastro do canal público no programa de afiliados");
  if (!product.creativeReviewStatus) throw new Error("Conclua a revisão visual antes de publicar");

  let campaignPackage: CampaignPackage;
  try {
    campaignPackage = JSON.parse(product.campaignPackage || "") as CampaignPackage;
  } catch {
    throw new Error("Prepare novamente o pacote antes de publicar");
  }
  const blockers = (campaignPackage.missingToPublish ?? [])
    .filter((field) => field !== "aprovação final do owner");
  if (blockers.length) throw new Error(`Resolva antes de publicar: ${blockers.join(", ")}`);
  const message = String(campaignPackage.copy ?? "").trim();
  if (!message || message.length > 4096 || !message.includes(product.affiliateUrl)) {
    throw new Error("A prévia do Telegram está inválida ou não contém o link afiliado confirmado");
  }

  const existing = await db.select().from(telegramPublicationRequests)
    .where(eq(telegramPublicationRequests.productId, productId));
  const active = existing.find((row) => ACTIVE_STATUSES.includes(row.status));
  if (active) return telegramPublicationState();

  const now = new Date().toISOString();
  await db.insert(telegramPublicationRequests).values({
    id: crypto.randomUUID(),
    productId,
    status: "queued",
    chatId: DEFAULT_CHAT_ID,
    messageText: message,
    affiliateUrl: product.affiliateUrl,
    imageUrl: product.imageUrl,
    ownerApproved: 1,
    linkPreviewEnabled: 1,
    telegramMessageId: null,
    error: "",
    approvedAt: now,
    claimedAt: null,
    sentAt: null,
    createdAt: now,
    updatedAt: now,
  });
  return telegramPublicationState();
}

export async function claimTelegramPublication() {
  await ensureTelegramPublicationSchema();
  const db = getDb();
  const rows = await db.select().from(telegramPublicationRequests)
    .where(eq(telegramPublicationRequests.status, "queued"))
    .orderBy(asc(telegramPublicationRequests.createdAt)).limit(1);
  const item = rows[0];
  if (!item) return { items: [] };
  const now = new Date().toISOString();
  await db.update(telegramPublicationRequests).set({
    status: "publishing",
    claimedAt: now,
    updatedAt: now,
  }).where(eq(telegramPublicationRequests.id, item.id));
  return { items: [{
    id: item.id,
    productId: item.productId,
    chatId: item.chatId,
    messageText: item.messageText,
    linkPreviewEnabled: Boolean(item.linkPreviewEnabled),
    ownerApproved: Boolean(item.ownerApproved),
  }] };
}

export async function applyTelegramPublicationResult(input: {
  requestId: string;
  status: "sent" | "failed";
  messageId: number | null;
  error: string;
}) {
  await ensureTelegramPublicationSchema();
  const db = getDb();
  const rows = await db.select().from(telegramPublicationRequests)
    .where(eq(telegramPublicationRequests.id, input.requestId)).limit(1);
  if (!rows[0] || rows[0].status !== "publishing") throw new Error("Solicitação não está reservada para publicação");
  const now = new Date().toISOString();
  await db.update(telegramPublicationRequests).set({
    status: input.status,
    telegramMessageId: input.status === "sent" ? input.messageId : null,
    error: input.status === "failed" ? input.error.slice(0, 500) : "",
    sentAt: input.status === "sent" ? now : null,
    updatedAt: now,
  }).where(eq(telegramPublicationRequests.id, input.requestId));
  return telegramPublicationState();
}

export async function retryTelegramPublication(requestId: string) {
  await ensureTelegramPublicationSchema();
  const db = getDb();
  const rows = await db.select().from(telegramPublicationRequests)
    .where(eq(telegramPublicationRequests.id, requestId)).limit(1);
  if (!rows[0] || rows[0].status !== "failed") throw new Error("Somente envios com falha podem ser reenviados");
  await db.update(telegramPublicationRequests).set({
    status: "queued", error: "", claimedAt: null, updatedAt: new Date().toISOString(),
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
    claimed_at TEXT, sent_at TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL
  )`).run();
  await env.DB.prepare("CREATE INDEX IF NOT EXISTS telegram_publication_status_idx ON telegram_publication_requests(status)").run();
  await env.DB.prepare("CREATE INDEX IF NOT EXISTS telegram_publication_product_idx ON telegram_publication_requests(product_id)").run();
}

function publicPublication(item: typeof telegramPublicationRequests.$inferSelect) {
  return {
    id: item.id,
    productId: item.productId,
    status: item.status,
    chatId: item.chatId,
    messageText: item.messageText,
    imageUrl: item.imageUrl,
    linkPreviewEnabled: Boolean(item.linkPreviewEnabled),
    telegramMessageId: item.telegramMessageId,
    error: item.error,
    approvedAt: item.approvedAt,
    sentAt: item.sentAt,
    updatedAt: item.updatedAt,
  };
}

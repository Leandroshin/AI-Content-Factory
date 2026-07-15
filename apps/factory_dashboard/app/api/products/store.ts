import { desc, eq, inArray } from "drizzle-orm";
import { getDb } from "../../../db";
import { productIntakeRequests } from "../../../db/schema";
import { upsertOpportunity } from "../dashboard/store";

export type ProductIntakeStatus = "queued" | "analyzing" | "completed" | "needs_input" | "blocked";

export type ProductWorkerResult = {
  requestId: string;
  status: Exclude<ProductIntakeStatus, "queued" | "analyzing">;
  title: string;
  imageUrl: string;
  analysisSummary: string;
  missingFields: string[];
  score: number;
  confidence: number;
  risk: string;
  nextAction: string;
  promiseReview?: string;
  creativeRecommendation?: string;
  commissionNotes?: string;
  funnelSuggestion?: string;
  affiliateReadiness?: string;
};

export type ProductIntakeInput = {
  productUrl: string;
  affiliateUrl: string;
  evidenceUrl: string;
  language: string;
  sourceKind: string;
  ownerNotes: string;
  targetChannel: string;
  trackingLabel: string;
  channelRegistered: boolean;
  marketplace: string;
};

export type CampaignPackage = {
  status: "draft_ready" | "blocked";
  product: string;
  promise: string;
  creative: string;
  channel: string;
  copy: string;
  risk: string;
  estimatedCost: string;
  missingToPublish: string[];
  publicationStatus: "blocked";
  generatedAt: string;
  organicBrief?: OrganicCampaignBrief;
};

export type OrganicCampaignBrief = {
  status: "ready_for_owner_review" | "blocked";
  goal: string;
  audience: string;
  angle: string;
  format: string;
  channel: string;
  draftCopy: string;
  disclosure: string;
  productionChecklist: string[];
  metricsToCollect: string[];
  missingBeforeProduction: string[];
  providerStatus: "not_called";
  publicationStatus: "blocked";
  generatedAt: string;
};

export async function createProductIntake(input: ProductIntakeInput) {
  const db = getDb();
  await ensureProductSchema();
  const existing = await db.select().from(productIntakeRequests).where(eq(productIntakeRequests.productUrl, input.productUrl)).limit(1);
  const now = new Date().toISOString();
  const id = existing[0]?.id ?? crypto.randomUUID();
  const values = {
    id,
    productUrl: input.productUrl,
    affiliateUrl: input.affiliateUrl,
    evidenceUrl: input.evidenceUrl,
    language: input.language,
    sourceKind: input.sourceKind,
    ownerNotes: input.ownerNotes,
    targetChannel: input.targetChannel,
    trackingLabel: input.trackingLabel,
    channelRegistered: input.channelRegistered ? 1 : 0,
    marketplace: input.marketplace,
    status: "queued",
    productName: existing[0]?.productName ?? "",
    imageUrl: existing[0]?.imageUrl ?? "",
    analysisSummary: input.ownerNotes
      ? `Aguardando coleta segura. Contexto do owner: ${input.ownerNotes}`
      : "Aguardando coleta segura dos dados do produto.",
    campaignPackage: null,
    missingFields: "[]",
    submittedAt: existing[0]?.submittedAt ?? now,
    updatedAt: now,
  };
  await db.insert(productIntakeRequests).values(values).onConflictDoUpdate({
    target: productIntakeRequests.id,
    set: values,
  });
  await upsertOpportunity({
    id: `product-intake-${id}`,
    title: `Produto para analisar · ${input.marketplace}`,
    source: "Product Intake",
    channel: "Achados Baratos BR",
    category: "Produto para analisar",
    summary: `${input.sourceKind === "sales_page" ? "Página de venda" : "Página de produto"} recebida. A fábrica ainda não validou preço, imagem, demanda ou vínculo afiliado.`,
    priority: "medium",
    score: 0,
    confidence: 0,
    risk: "Médio: dados ainda não coletados; nenhuma publicação está autorizada.",
    nextAction: "Aguardar a coleta e a análise dos funcionários.",
    updatedAt: now,
    sources: [
      { id: `product-intake-${id}-source-1`, label: `${input.sourceKind === "sales_page" ? "Página de venda" : "Página do produto"} em ${input.marketplace}`, url: input.productUrl, sourceType: "marketplace", publishedAt: null },
      ...(input.evidenceUrl ? [{ id: `product-intake-${id}-source-2`, label: "Evidência adicional informada pelo owner", url: input.evidenceUrl, sourceType: "reference" as const, publishedAt: null }] : []),
    ],
  });
  return productIntakeState();
}

export async function productIntakeState() {
  const db = getDb();
  await ensureProductSchema();
  const items = await db.select().from(productIntakeRequests).orderBy(desc(productIntakeRequests.updatedAt)).limit(50);
  return { items: items.map(publicItem) };
}

export async function productWorkerQueue(limit = 10) {
  const db = getDb();
  await ensureProductSchema();
  const items = await db.select().from(productIntakeRequests)
    .where(inArray(productIntakeRequests.status, ["queued", "analyzing"]))
    .orderBy(productIntakeRequests.submittedAt)
    .limit(Math.max(1, Math.min(10, limit)));
  return { items: items.map((item) => ({
    id: item.id,
    productUrl: item.productUrl,
    affiliateUrl: item.affiliateUrl,
    marketplace: item.marketplace,
    status: item.status,
    evidenceUrl: item.evidenceUrl ?? "",
    language: item.language ?? "",
    sourceKind: item.sourceKind ?? "product_page",
    ownerNotes: item.ownerNotes ?? "",
    targetChannel: item.targetChannel ?? "telegram_public",
    trackingLabel: item.trackingLabel ?? "telegram_public",
    channelRegistered: Boolean(item.channelRegistered),
  })) };
}

export async function prepareCampaignPackage(productId: string) {
  const db = getDb();
  await ensureProductSchema();
  const existing = await db.select().from(productIntakeRequests).where(eq(productIntakeRequests.id, productId)).limit(1);
  const item = existing[0];
  if (!item) throw new Error("Product intake request was not found");
  if (!["completed", "needs_input"].includes(item.status)) throw new Error("A análise precisa terminar antes do pacote de campanha");

  const now = new Date().toISOString();
  const missing = parseMissingFields(item.missingFields);
  if (!item.affiliateUrl) missing.push("link afiliado validado");
  if (item.marketplace === "Mercado Livre" && !item.channelRegistered) {
    missing.push("canal público cadastrado no programa de afiliados do Mercado Livre");
  }
  missing.push("aprovação final do owner");
  const missingToPublish = [...new Set(missing.map((field) => field.replaceAll("_", " ")))];
  const isSalesPage = (item.sourceKind ?? "product_page") === "sales_page";
  const product = item.productName || `Produto em ${item.marketplace}`;
  const campaignPackage: CampaignPackage = {
    status: missingToPublish.length > 1 ? "blocked" : "draft_ready",
    product,
    promise: item.promiseReview || "Promessa ainda não confirmada pela análise.",
    creative: item.creativeRecommendation || "Criativo ainda depende de revisão visual.",
    channel: isSalesPage ? "Landing própria + Telegram" : channelName(item.targetChannel),
    copy: `${product}. Confira preço, disponibilidade e condições na página oficial. Como afiliado, posso receber comissão por compras feitas pelo link, sem custo extra para você.${item.trackingLabel ? ` Etiqueta de rastreio: ${item.trackingLabel}.` : ""}`,
    risk: missingToPublish.length > 3
      ? "Alto: existem pendências comerciais ou de evidência antes de publicar."
      : "Médio: conferir rastreamento, condições da oferta e revisão final.",
    estimatedCost: "US$ 0,00 nesta preparação",
    missingToPublish,
    publicationStatus: "blocked",
    generatedAt: now,
  };
  await db.update(productIntakeRequests).set({
    campaignPackage: JSON.stringify(campaignPackage),
    updatedAt: now,
  }).where(eq(productIntakeRequests.id, productId));
  return productIntakeState();
}

export async function retryProductIntake(productId: string) {
  const db = getDb();
  await ensureProductSchema();
  const existing = await db.select().from(productIntakeRequests).where(eq(productIntakeRequests.id, productId)).limit(1);
  const item = existing[0];
  if (!item) throw new Error("Product intake request was not found");
  if (!["needs_input", "blocked"].includes(item.status)) throw new Error("Somente análises com pendências podem voltar para coleta");

  await db.update(productIntakeRequests).set({
    status: "queued",
    campaignPackage: null,
    missingFields: JSON.stringify([]),
    updatedAt: new Date().toISOString(),
  }).where(eq(productIntakeRequests.id, productId));
  return productIntakeState();
}

export async function prepareOrganicBrief(productId: string) {
  const db = getDb();
  await ensureProductSchema();
  const existing = await db.select().from(productIntakeRequests).where(eq(productIntakeRequests.id, productId)).limit(1);
  const item = existing[0];
  if (!item) throw new Error("Product intake request was not found");
  if (!item.campaignPackage) throw new Error("Prepare e compare o pacote antes de criar o briefing");

  let campaignPackage: CampaignPackage;
  try {
    campaignPackage = JSON.parse(item.campaignPackage) as CampaignPackage;
  } catch {
    throw new Error("O pacote de campanha precisa ser preparado novamente");
  }

  const now = new Date().toISOString();
  const missingBeforeProduction = campaignPackage.missingToPublish
    .filter((field) => field !== "aprovação final do owner");
  const isSalesPage = (item.sourceKind ?? "product_page") === "sales_page";
  const organicBrief: OrganicCampaignBrief = {
    status: missingBeforeProduction.length ? "blocked" : "ready_for_owner_review",
    goal: isSalesPage
      ? "Validar interesse orgânico antes de investir em tráfego pago."
      : "Validar cliques e intenção de compra com distribuição orgânica controlada.",
    audience: isSalesPage
      ? "Pessoas com problema compatível com a promessa, sem segmentação sensível ou alegação não comprovada."
      : "Seguidores interessados na categoria do produto e em ofertas verificáveis.",
    angle: campaignPackage.promise,
    format: campaignPackage.creative,
    channel: campaignPackage.channel,
    draftCopy: campaignPackage.copy,
    disclosure: "Como afiliado, posso receber comissão por compras feitas pelo link, sem custo extra para você.",
    productionChecklist: [
      "Confirmar preço, disponibilidade e condições na fonte original.",
      "Usar somente imagem autorizada, própria ou revisada pelo Creative Review.",
      "Manter promessa, oferta e disclosure legíveis no criativo.",
      "Submeter o material final à revisão do owner antes de publicar.",
    ],
    metricsToCollect: ["visualizações", "cliques no link", "CTR", "conversões", "comissão", "custo", "ROI"],
    missingBeforeProduction,
    providerStatus: "not_called",
    publicationStatus: "blocked",
    generatedAt: now,
  };
  campaignPackage.organicBrief = organicBrief;
  await db.update(productIntakeRequests).set({
    campaignPackage: JSON.stringify(campaignPackage),
    updatedAt: now,
  }).where(eq(productIntakeRequests.id, productId));
  return productIntakeState();
}

export async function applyProductWorkerResult(input: ProductWorkerResult) {
  const db = getDb();
  await ensureProductSchema();
  const existing = await db.select().from(productIntakeRequests).where(eq(productIntakeRequests.id, input.requestId)).limit(1);
  if (!existing[0]) throw new Error("Product intake request was not found");
  const now = new Date().toISOString();
  await db.update(productIntakeRequests).set({
    status: input.status,
    productName: input.title,
    imageUrl: input.imageUrl,
    analysisSummary: input.analysisSummary,
    promiseReview: input.promiseReview ?? "",
    creativeRecommendation: input.creativeRecommendation ?? "",
    commissionNotes: input.commissionNotes ?? "",
    funnelSuggestion: input.funnelSuggestion ?? "",
    affiliateReadiness: input.affiliateReadiness ?? "",
    campaignPackage: null,
    missingFields: JSON.stringify(input.missingFields),
    updatedAt: now,
  }).where(eq(productIntakeRequests.id, input.requestId));
  const ready = input.status === "completed";
  await upsertOpportunity({
    id: `product-intake-${input.requestId}`,
    title: input.title,
    source: "Product Research",
    channel: "Achados Baratos BR",
    category: ready ? "Produto analisado" : "Produto para completar",
    summary: input.analysisSummary,
    priority: input.status === "blocked" ? "low" : input.score >= 80 ? "high" : "medium",
    score: input.score,
    confidence: input.confidence,
    risk: input.risk,
    nextAction: input.nextAction,
    updatedAt: now,
    sources: [{ id: `product-intake-${input.requestId}-source-1`, label: `Página do produto em ${existing[0].marketplace}`, url: existing[0].productUrl, sourceType: "marketplace", publishedAt: null }],
  });
  return productIntakeState();
}

async function ensureProductSchema() {
  const { env } = await import("cloudflare:workers");
  await env.DB.prepare("CREATE TABLE IF NOT EXISTS product_intake_requests (id TEXT PRIMARY KEY, product_url TEXT NOT NULL, affiliate_url TEXT NOT NULL, marketplace TEXT NOT NULL, status TEXT NOT NULL, product_name TEXT NOT NULL, image_url TEXT NOT NULL, analysis_summary TEXT NOT NULL, missing_fields TEXT NOT NULL, submitted_at TEXT NOT NULL, updated_at TEXT NOT NULL)").run();
  await addColumnIfMissing("product_intake_requests", "evidence_url", "TEXT");
  await addColumnIfMissing("product_intake_requests", "language", "TEXT");
  await addColumnIfMissing("product_intake_requests", "source_kind", "TEXT");
  await addColumnIfMissing("product_intake_requests", "owner_notes", "TEXT");
  await addColumnIfMissing("product_intake_requests", "target_channel", "TEXT NOT NULL DEFAULT 'telegram_public'");
  await addColumnIfMissing("product_intake_requests", "tracking_label", "TEXT NOT NULL DEFAULT 'telegram_public'");
  await addColumnIfMissing("product_intake_requests", "channel_registered", "INTEGER NOT NULL DEFAULT 0");
  await addColumnIfMissing("product_intake_requests", "promise_review", "TEXT");
  await addColumnIfMissing("product_intake_requests", "creative_recommendation", "TEXT");
  await addColumnIfMissing("product_intake_requests", "commission_notes", "TEXT");
  await addColumnIfMissing("product_intake_requests", "funnel_suggestion", "TEXT");
  await addColumnIfMissing("product_intake_requests", "affiliate_readiness", "TEXT");
  await addColumnIfMissing("product_intake_requests", "campaign_package", "TEXT");
  await env.DB.prepare("CREATE INDEX IF NOT EXISTS product_intake_status_idx ON product_intake_requests(status)").run();
}

async function addColumnIfMissing(table: string, column: string, definition: string) {
  const { env } = await import("cloudflare:workers");
  try {
    await env.DB.prepare(`ALTER TABLE ${table} ADD COLUMN ${column} ${definition}`).run();
  } catch (error) {
    const message = error instanceof Error ? error.message.toLowerCase() : "";
    if (!message.includes("duplicate column") && !message.includes("already exists")) throw error;
  }
}

function publicItem(item: typeof productIntakeRequests.$inferSelect) {
  const missingFields = parseMissingFields(item.missingFields);
  let campaignPackage: CampaignPackage | null = null;
  try { campaignPackage = item.campaignPackage ? JSON.parse(item.campaignPackage) as CampaignPackage : null; } catch { campaignPackage = null; }
  return {
    id: item.id,
    productUrl: item.productUrl,
    evidenceUrl: item.evidenceUrl ?? "",
    language: item.language ?? "",
    sourceKind: item.sourceKind ?? "product_page",
    ownerNotes: item.ownerNotes ?? "",
    targetChannel: item.targetChannel ?? "telegram_public",
    trackingLabel: item.trackingLabel ?? "telegram_public",
    channelRegistered: Boolean(item.channelRegistered),
    affiliateProvided: Boolean(item.affiliateUrl),
    marketplace: item.marketplace,
    status: item.status as ProductIntakeStatus,
    productName: item.productName,
    imageUrl: item.imageUrl,
    analysisSummary: item.analysisSummary,
    promiseReview: item.promiseReview ?? "",
    creativeRecommendation: item.creativeRecommendation ?? "",
    commissionNotes: item.commissionNotes ?? "",
    funnelSuggestion: item.funnelSuggestion ?? "",
    affiliateReadiness: item.affiliateReadiness ?? "",
    campaignPackage,
    missingFields,
    submittedAt: item.submittedAt,
    updatedAt: item.updatedAt,
  };
}

function parseMissingFields(value: string) {
  try { return JSON.parse(value) as string[]; } catch { return []; }
}

function channelName(value: string | null) {
  if (value === "whatsapp_public") return "WhatsApp público (preparação manual)";
  if (value === "instagram_public") return "Instagram público";
  return "Telegram público";
}

import { completeCommercialData, createProductIntake, prepareCampaignPackage, prepareOrganicBrief, productIntakeState, retryProductIntake } from "./store";

const MAX_BODY_BYTES = 8_000;
const MARKETPLACES = [
  { name: "Amazon Brasil", domains: ["amazon.com.br"] },
  { name: "Mercado Livre", domains: ["mercadolivre.com.br", "mercadolivre.com", "meli.la"] },
  { name: "Shopee", domains: ["shopee.com.br"] },
  { name: "Adidas", domains: ["adidas.com.br"] },
  { name: "Digistore24", domains: ["digistore24.com", "digistore24-app.com"] },
  { name: "Braip", domains: ["braip.com", "ev.braip.com"] },
] as const;

const LANGUAGES = new Set(["pt-BR", "en", "es", "unknown"]);
const SOURCE_KINDS = new Set(["product_page", "sales_page"]);
const TARGET_CHANNELS = new Set(["telegram_public", "whatsapp_public", "instagram_public"]);

export async function GET() {
  return Response.json(await productIntakeState());
}

export async function POST(request: Request) {
  const raw = await request.text();
  if (new TextEncoder().encode(raw).byteLength > MAX_BODY_BYTES) return Response.json({ error: "Payload too large" }, { status: 413 });
  try {
    const body = JSON.parse(raw) as Record<string, unknown>;
    const product = publicHttps(body.productUrl, "URL do produto");
    const marketplace = marketplaceFor(product.hostname);
    if (!marketplace) throw new Error("Use uma URL de uma loja reconhecida: Amazon Brasil, Mercado Livre, Shopee, Adidas, Digistore24 ou Braip");
    const affiliateUrl = body.affiliateUrl
      ? publicHttps(body.affiliateUrl, "Link afiliado").toString()
      : product.hostname.toLowerCase() === "meli.la" ? product.toString() : "";
    const evidenceUrl = body.evidenceUrl ? publicHttps(body.evidenceUrl, "URL de evidência").toString() : "";
    const language = enumValue(body.language, LANGUAGES, "Idioma", "unknown");
    const sourceKind = enumValue(body.sourceKind, SOURCE_KINDS, "Tipo de página", "product_page");
    const ownerNotes = optionalText(body.ownerNotes, "Contexto", 800);
    const targetChannel = enumValue(body.targetChannel, TARGET_CHANNELS, "Canal", "telegram_public");
    const trackingLabel = trackingLabelValue(body.trackingLabel, targetChannel);
    const channelRegistered = body.channelRegistered === true;
    return Response.json(await createProductIntake({
      productUrl: product.toString(),
      affiliateUrl,
      evidenceUrl,
      language,
      sourceKind,
      ownerNotes,
      targetChannel,
      trackingLabel,
      channelRegistered,
      marketplace,
    }), { status: 202 });
  } catch (error) {
    return Response.json({ error: error instanceof Error ? error.message : "Dados inválidos" }, { status: 400 });
  }
}

export async function PATCH(request: Request) {
  try {
    const body = await request.json() as Record<string, unknown>;
    if (typeof body.productId !== "string" || !body.productId.trim()) throw new Error("Produto inválido");
    if (body.action === "retry_analysis") return Response.json(await retryProductIntake(body.productId.trim()));
    if (body.action === "prepare_campaign") return Response.json(await prepareCampaignPackage(body.productId.trim()));
    if (body.action === "prepare_organic_brief") return Response.json(await prepareOrganicBrief(body.productId.trim()));
    if (body.action === "complete_commercial") return Response.json(await completeCommercialData(body.productId.trim(), {
      currentPrice: finiteNumber(body.currentPrice, "Preço atual"),
      oldPrice: body.oldPrice == null || body.oldPrice === "" ? null : finiteNumber(body.oldPrice, "Preço anterior"),
      commissionConfirmed: body.commissionConfirmed === true,
      creativeReviewStatus: body.creativeReviewStatus === "approved_custom" ? "approved_custom" : "official_link_preview",
      channelRegistered: body.channelRegistered === true,
    }));
    throw new Error("Ação de campanha inválida");
  } catch (error) {
    return Response.json({ error: error instanceof Error ? error.message : "Dados inválidos" }, { status: 400 });
  }
}

function finiteNumber(value: unknown, label: string) {
  const number = typeof value === "number" ? value : Number(String(value).replace(",", "."));
  if (!Number.isFinite(number)) throw new Error(`${label} inválido`);
  return number;
}

function enumValue(value: unknown, allowed: Set<string>, label: string, fallback: string) {
  if (value == null || value === "") return fallback;
  if (typeof value !== "string" || !allowed.has(value)) throw new Error(`${label} inválido`);
  return value;
}

function optionalText(value: unknown, label: string, max: number) {
  if (value == null || value === "") return "";
  if (typeof value !== "string" || value.length > max) throw new Error(`${label} inválido`);
  return value.trim();
}

function trackingLabelValue(value: unknown, fallback: string) {
  if (value == null || value === "") return fallback;
  if (typeof value !== "string" || !/^[a-z0-9_-]{2,48}$/i.test(value)) throw new Error("Etiqueta de rastreio inválida");
  return value;
}

function publicHttps(value: unknown, label: string) {
  if (typeof value !== "string" || !value.trim() || value.length > 1_500) throw new Error(`${label} inválida`);
  const url = new URL(value.trim());
  if (url.protocol !== "https:" || url.username || url.password || !url.hostname) throw new Error(`${label} deve usar HTTPS público`);
  return url;
}

function marketplaceFor(hostname: string) {
  const host = hostname.toLowerCase();
  return MARKETPLACES.find((marketplace) => marketplace.domains.some((domain) => host === domain || host.endsWith(`.${domain}`)))?.name ?? "";
}

import { createProductIntake, prepareCampaignPackage, prepareOrganicBrief, productIntakeState } from "./store";

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
    return Response.json(await createProductIntake({
      productUrl: product.toString(),
      affiliateUrl,
      evidenceUrl,
      language,
      sourceKind,
      ownerNotes,
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
    if (body.action === "prepare_campaign") return Response.json(await prepareCampaignPackage(body.productId.trim()));
    if (body.action === "prepare_organic_brief") return Response.json(await prepareOrganicBrief(body.productId.trim()));
    throw new Error("Ação de campanha inválida");
  } catch (error) {
    return Response.json({ error: error instanceof Error ? error.message : "Dados inválidos" }, { status: 400 });
  }
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

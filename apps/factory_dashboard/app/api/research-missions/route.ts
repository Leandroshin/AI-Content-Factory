import { archiveResearchMission, createResearchMission, researchMissionState } from "./store";

const MARKETPLACES = new Set(["mercado_livre", "amazon", "shopee"]);
const TIMEFRAMES = new Set(["today", "week", "evergreen"]);
const CHANNELS = new Set(["telegram_public", "whatsapp_public", "youtube", "instagram"]);

export async function GET() {
  return Response.json(await researchMissionState());
}

export async function POST(request: Request) {
  try {
    const body = await request.json() as Record<string, unknown>;
    const goal = text(body.goal, "Objetivo", 120);
    const marketplaces = Array.isArray(body.marketplaces)
      ? [...new Set(body.marketplaces.map((value) => text(value, "Marketplace", 30)).filter((value) => MARKETPLACES.has(value)))]
      : [];
    if (!marketplaces.length) throw new Error("Escolha pelo menos um marketplace");
    const resultLimit = integer(body.resultLimit, "Quantidade", 3, 10);
    const maxPrice = body.maxPrice == null || body.maxPrice === "" ? null : decimal(body.maxPrice, "Preço máximo", 1, 1_000_000);
    const timeframe = member(body.timeframe, TIMEFRAMES, "Período");
    const targetChannel = member(body.targetChannel, CHANNELS, "Canal");
    const category = optionalText(body.category, "Categoria", 80);
    return Response.json(await createResearchMission({ goal, marketplaces, category, maxPrice, timeframe, resultLimit, targetChannel }), { status: 202 });
  } catch (error) {
    return Response.json({ error: error instanceof Error ? error.message : "Dados inválidos" }, { status: 400 });
  }
}

export async function DELETE(request: Request) {
  try {
    const body = await request.json() as Record<string, unknown>;
    const missionId = text(body.missionId, "Pesquisa", 80);
    return Response.json(await archiveResearchMission(missionId));
  } catch (error) {
    return Response.json({ error: error instanceof Error ? error.message : "Dados inválidos" }, { status: 400 });
  }
}

function text(value: unknown, label: string, max: number) {
  if (typeof value !== "string" || value.trim().length < 2 || value.length > max) throw new Error(`${label} inválido`);
  return value.trim();
}
function optionalText(value: unknown, label: string, max: number) { return value == null || value === "" ? "" : text(value, label, max); }
function integer(value: unknown, label: string, min: number, max: number) {
  const number = Number(value);
  if (!Number.isInteger(number) || number < min || number > max) throw new Error(`${label} inválida`);
  return number;
}
function decimal(value: unknown, label: string, min: number, max: number) {
  const number = Number(value);
  if (!Number.isFinite(number) || number < min || number > max) throw new Error(`${label} inválido`);
  return number;
}
function member(value: unknown, allowed: Set<string>, label: string) {
  if (typeof value !== "string" || !allowed.has(value)) throw new Error(`${label} inválido`);
  return value;
}

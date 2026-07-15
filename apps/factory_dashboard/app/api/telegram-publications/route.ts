import { queueTelegramPublication, retryTelegramPublication, telegramPublicationState } from "./store";

export async function GET() {
  return Response.json(await telegramPublicationState());
}

export async function POST(request: Request) {
  try {
    const body = await request.json() as Record<string, unknown>;
    if (body.confirmation !== "PUBLICAR NO TELEGRAM") throw new Error("Revise a prévia e confirme a publicação no Telegram");
    if (typeof body.productId !== "string" || !body.productId.trim()) throw new Error("Produto inválido");
    return Response.json(await queueTelegramPublication(body.productId.trim()), { status: 202 });
  } catch (error) {
    return Response.json({ error: error instanceof Error ? error.message : "Dados inválidos" }, { status: 400 });
  }
}

export async function PATCH(request: Request) {
  try {
    const body = await request.json() as Record<string, unknown>;
    if (body.action !== "retry" || typeof body.requestId !== "string") throw new Error("Ação inválida");
    return Response.json(await retryTelegramPublication(body.requestId.trim()));
  } catch (error) {
    return Response.json({ error: error instanceof Error ? error.message : "Dados inválidos" }, { status: 400 });
  }
}

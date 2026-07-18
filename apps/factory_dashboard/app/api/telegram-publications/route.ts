import { approveTelegramPublication, prepareEditorialTelegramCandidate, queueTelegramPublication, retryTelegramPublication, telegramPublicationState } from "./store";

export async function GET() {
  return Response.json(await telegramPublicationState());
}

export async function POST(request: Request) {
  try {
    const body = await request.json() as Record<string, unknown>;
    if (body.confirmation !== "PREPARAR CANDIDATO") throw new Error("Confirme somente a preparação do candidato");
    if (body.action === "prepare_editorial") {
      return Response.json(await prepareEditorialTelegramCandidate(), { status: 202 });
    }
    if (body.action !== "prepare_product" || typeof body.productId !== "string" || !body.productId.trim()) throw new Error("Ação ou produto inválido");
    return Response.json(await queueTelegramPublication(body.productId.trim()), { status: 202 });
  } catch (error) {
    return Response.json({ error: error instanceof Error ? error.message : "Dados inválidos" }, { status: 400 });
  }
}

export async function PATCH(request: Request) {
  try {
    const body = await request.json() as Record<string, unknown>;
    if (typeof body.requestId !== "string" || !body.requestId.trim()) throw new Error("Solicitação inválida");
    if (body.action === "approve") {
      if (body.confirmation !== "APROVAR PUBLICACAO TELEGRAM") throw new Error("A aprovação final exige confirmação explícita");
      return Response.json(await approveTelegramPublication(body.requestId.trim()));
    }
    if (body.action === "retry") return Response.json(await retryTelegramPublication(body.requestId.trim()));
    throw new Error("Ação inválida");
  } catch (error) {
    return Response.json({ error: error instanceof Error ? error.message : "Dados inválidos" }, { status: 400 });
  }
}

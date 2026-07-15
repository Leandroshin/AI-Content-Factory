import { requireDashboardIntake } from "../_shared";
import { applyTelegramPublicationResult, claimTelegramPublication } from "../../telegram-publications/store";

export async function GET(request: Request) {
  const unauthorized = await requireDashboardIntake(request, "Telegram publication");
  if (unauthorized) return unauthorized;
  return Response.json(await claimTelegramPublication());
}

export async function POST(request: Request) {
  const unauthorized = await requireDashboardIntake(request, "Telegram publication");
  if (unauthorized) return unauthorized;
  try {
    const raw = await request.text();
    if (new TextEncoder().encode(raw).byteLength > 4_000) return Response.json({ error: "Payload too large" }, { status: 413 });
    const body = JSON.parse(raw) as Record<string, unknown>;
    if (typeof body.requestId !== "string" || !body.requestId.trim()) throw new Error("requestId inválido");
    if (body.status !== "sent" && body.status !== "failed") throw new Error("status inválido");
    const messageId = body.messageId == null ? null : Number(body.messageId);
    if (messageId != null && (!Number.isInteger(messageId) || messageId <= 0)) throw new Error("messageId inválido");
    const error = typeof body.error === "string" ? body.error : "";
    return Response.json(await applyTelegramPublicationResult({
      requestId: body.requestId.trim(), status: body.status, messageId, error,
    }), { status: 202 });
  } catch (error) {
    return Response.json({ error: error instanceof Error ? error.message : "Dados inválidos" }, { status: 400 });
  }
}

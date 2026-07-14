import { requireDashboardIntake } from "../_shared";
import { applyResearchMissionResult, researchMissionQueue, type ResearchMissionWorkerResult } from "../../research-missions/store";

export async function GET(request: Request) {
  const unauthorized = await requireDashboardIntake(request, "Product research worker");
  if (unauthorized) return unauthorized;
  return Response.json(await researchMissionQueue());
}

export async function POST(request: Request) {
  const unauthorized = await requireDashboardIntake(request, "Product research worker");
  if (unauthorized) return unauthorized;
  try {
    const body = await request.json() as Record<string, unknown>;
    const status = String(body.status ?? "");
    if (!body.missionId || !["review", "needs_input", "blocked"].includes(status)) throw new Error("Resultado inválido");
    const input: ResearchMissionWorkerResult = {
      missionId: String(body.missionId),
      status: status as ResearchMissionWorkerResult["status"],
      report: body.report && typeof body.report === "object" ? body.report as Record<string, unknown> : {},
      error: typeof body.error === "string" ? body.error.slice(0, 500) : "",
    };
    return Response.json({ accepted: true, state: await applyResearchMissionResult(input) }, { status: 202 });
  } catch (error) {
    return Response.json({ error: error instanceof Error ? error.message : "Dados inválidos" }, { status: 400 });
  }
}

import { selectProviderPlan, updateOpportunity } from "../dashboard/store";

export async function POST(request: Request) {
  const body = (await request.json()) as { id?: string; action?: string; planId?: string };
  if (!body.id || !["approve", "reject", "discard", "approve_media", "select_provider_plan"].includes(body.action ?? "")) {
    return Response.json({ error: "Invalid decision" }, { status: 400 });
  }
  try {
    if (body.action === "select_provider_plan") {
      if (body.planId !== "local_free" && body.planId !== "hybrid_quality") return Response.json({ error: "Invalid provider plan" }, { status: 400 });
      return Response.json(await selectProviderPlan(body.id, body.planId));
    }
    return Response.json(await updateOpportunity(body.id, body.action as "approve" | "reject" | "discard" | "approve_media"));
  } catch (error) {
    return Response.json({ error: error instanceof Error ? error.message : "Decision unavailable" }, { status: 503 });
  }
}

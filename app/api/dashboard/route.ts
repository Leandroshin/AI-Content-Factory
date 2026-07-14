import { dashboardState } from "./store";

export async function GET() {
  try {
    return Response.json(await dashboardState());
  } catch (error) {
    return Response.json({ error: error instanceof Error ? error.message : "Dashboard unavailable" }, { status: 503 });
  }
}

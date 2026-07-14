import { authenticatedOpportunityIntake } from "../_shared";

export async function POST(request: Request) {
  return authenticatedOpportunityIntake(request, "Gaming");
}

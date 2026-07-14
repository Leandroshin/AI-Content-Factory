import type { Metadata } from "next";
import { DashboardClient } from "./components/DashboardClient";
import { getChatGPTUser } from "./chatgpt-auth";

export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "Central de Comando | AI Content Factory",
  description: "Cockpit operacional da fábrica de conteúdo e afiliados.",
};

export default async function Home() {
  const user = await getChatGPTUser();
  const operator = user?.fullName ?? user?.email ?? "Leandro Shin";

  return <DashboardClient operator={operator} authenticated={Boolean(user)} />;
}

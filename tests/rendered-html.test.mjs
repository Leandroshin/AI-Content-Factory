import assert from "node:assert/strict";
import test from "node:test";

test("factory dashboard source exposes the operational cockpit", async () => {
  const page = await import("node:fs/promises").then((fs) => fs.readFile(new URL("../app/page.tsx", import.meta.url), "utf8"));
  const client = await import("node:fs/promises").then((fs) => fs.readFile(new URL("../app/components/DashboardClient.tsx", import.meta.url), "utf8"));
  assert.match(page, /Central de Comando/);
  assert.match(page, /getChatGPTUser/);
  assert.match(client, /Aprovar rascunho/);
  assert.match(client, /Áudio, vídeo final, publicação e gastos exigem outras aprovações/);
  assert.match(client, /Fase Nova Games/);
  assert.match(client, /Achados Baratos BR/);
  assert.match(client, /Busca global da fábrica/);
  assert.match(client, /Tema do painel/);
  assert.match(client, /Matrix/);
  assert.match(client, /Fontes para conferência/);
  assert.match(client, /Adicionar produto/);
  assert.match(client, /Página de venda ou produto/);
  assert.match(client, /Link afiliado/);
  assert.match(client, /Evidência ou página de suporte/);
  assert.match(client, /Contexto para os funcionários/);
  assert.match(client, /Digistore24/);
  assert.match(client, /Braip/);
  assert.match(client, /Enviar para análise/);
  assert.match(client, /111 demonstrações técnicas aprovadas/);
  assert.match(client, /111\/111/);
  assert.match(client, /1\.817 verificações explícitas/);
  assert.doesNotMatch(client, /window\.print/);
});

test("production approval creates an authenticated MOCK review queue", async () => {
  const client = await import("node:fs/promises").then((fs) => fs.readFile(new URL("../app/components/DashboardClient.tsx", import.meta.url), "utf8"));
  const store = await import("node:fs/promises").then((fs) => fs.readFile(new URL("../app/api/dashboard/store.ts", import.meta.url), "utf8"));
  const route = await import("node:fs/promises").then((fs) => fs.readFile(new URL("../app/api/intake/production/route.ts", import.meta.url), "utf8"));
  assert.match(client, /Fila de produção e revisão/);
  assert.match(client, /RASCUNHO PARA REVISÃO/);
  assert.match(client, /Publicação: bloqueada/);
  assert.match(client, /Descartar rascunho/);
  assert.match(client, /badge=\{data\.productions\.length\}/);
  assert.match(client, /ProductionStatusDetail/);
  assert.match(client, /imagem real do produto ou notícia/i);
  assert.match(client, /pipelineSelected/);
  assert.match(store, /production_requests/);
  assert.match(store, /mode: "MOCK"/);
  assert.match(store, /publicationStatus: "blocked"/);
  assert.match(store, /Only review drafts can be discarded/);
  assert.match(route, /requireDashboardIntake/);
  assert.match(route, /review.*failed/s);
  assert.doesNotMatch(`${store}\n${route}`, /console\.(log|error)/);
});

test("second approval prepares media plans without providers or publication", async () => {
  const client = await import("node:fs/promises").then((fs) => fs.readFile(new URL("../app/components/DashboardClient.tsx", import.meta.url), "utf8"));
  const store = await import("node:fs/promises").then((fs) => fs.readFile(new URL("../app/api/dashboard/store.ts", import.meta.url), "utf8"));
  const route = await import("node:fs/promises").then((fs) => fs.readFile(new URL("../app/api/intake/media-production/route.ts", import.meta.url), "utf8"));
  assert.match(client, /Aprovar pré-produção MOCK/);
  assert.match(client, /PRÉ-PRODUÇÃO PARA REVISÃO/);
  assert.match(client, /Provider:.*não chamado/);
  assert.match(client, /porcentagem indica etapas concluídas, não tempo/i);
  assert.match(store, /media_production_requests/);
  assert.match(store, /Only reviewed scripts can enter media pre-production/);
  assert.match(store, /Monitoring routines require a concrete news item/);
  assert.match(store, /providerStatus: "not_called"/);
  assert.match(store, /finalAssetStatus: "not_generated"/);
  assert.match(route, /requireDashboardIntake/);
  assert.match(route, /media_review.*failed/s);
  assert.doesNotMatch(`${store}\n${route}`, /console\.(log|error)/);
});

test("third gate compares provider budgets without executing them", async () => {
  const client = await import("node:fs/promises").then((fs) => fs.readFile(new URL("../app/components/DashboardClient.tsx", import.meta.url), "utf8"));
  const store = await import("node:fs/promises").then((fs) => fs.readFile(new URL("../app/api/dashboard/store.ts", import.meta.url), "utf8"));
  const actions = await import("node:fs/promises").then((fs) => fs.readFile(new URL("../app/api/actions/route.ts", import.meta.url), "utf8"));
  assert.match(client, /TERCEIRO PORTÃO/);
  assert.match(client, /Escolha o orçamento, não a execução/);
  assert.match(client, /Selecionar plano gratuito/);
  assert.match(client, /Guardar para usar depois/);
  assert.match(client, /US\$ 0 gastos/);
  assert.match(store, /provider_plan_selections/);
  assert.match(store, /executionStatus: "blocked"/);
  assert.match(store, /ownerApprovedExecution: 0/);
  assert.match(store, /gemini_omni_flash/);
  assert.match(store, /Math\.round\(duration \* 10\) \/ 100/);
  assert.match(actions, /select_provider_plan/);
  assert.doesNotMatch(`${store}\n${actions}`, /fetch\(|axios|http:\/\//);
});

test("gaming radar intake stays authenticated and bounded", async () => {
  const route = await import("node:fs/promises").then((fs) => fs.readFile(new URL("../app/api/intake/gaming/route.ts", import.meta.url), "utf8"));
  const shared = await import("node:fs/promises").then((fs) => fs.readFile(new URL("../app/api/intake/_shared.ts", import.meta.url), "utf8"));
  assert.match(route, /authenticatedOpportunityIntake/);
  assert.match(shared, /DASHBOARD_INTAKE_TOKEN/);
  assert.match(shared, /constantTimeEqual/);
  assert.match(shared, /MAX_BODY_BYTES/);
  assert.match(shared, /public HTTPS/);
  assert.match(shared, /upsertOpportunity/);
  assert.doesNotMatch(route, /console\.(log|error)/);
  assert.doesNotMatch(shared, /console\.(log|error)/);
});

test("commerce intake reuses the same authenticated contract", async () => {
  const route = await import("node:fs/promises").then((fs) => fs.readFile(new URL("../app/api/intake/commerce/route.ts", import.meta.url), "utf8"));
  assert.match(route, /authenticatedOpportunityIntake/);
  assert.match(route, /Commerce/);
  assert.doesNotMatch(route, /token|secret|console\.(log|error)/i);
});

test("product intake separates owner input from the authenticated worker", async () => {
  const ownerRoute = await import("node:fs/promises").then((fs) => fs.readFile(new URL("../app/api/products/route.ts", import.meta.url), "utf8"));
  const workerRoute = await import("node:fs/promises").then((fs) => fs.readFile(new URL("../app/api/intake/products/route.ts", import.meta.url), "utf8"));
  const store = await import("node:fs/promises").then((fs) => fs.readFile(new URL("../app/api/products/store.ts", import.meta.url), "utf8"));
  assert.match(ownerRoute, /Amazon Brasil/);
  assert.match(ownerRoute, /Mercado Livre/);
  assert.match(ownerRoute, /meli\.la/);
  assert.match(ownerRoute, /Shopee/);
  assert.match(ownerRoute, /Adidas/);
  assert.match(ownerRoute, /Digistore24/);
  assert.match(ownerRoute, /Braip/);
  assert.match(ownerRoute, /Tipo de página/);
  assert.match(ownerRoute, /HTTPS público/);
  assert.match(ownerRoute, /product\.hostname\.toLowerCase\(\) === "meli\.la"/);
  assert.match(workerRoute, /requireDashboardIntake/);
  assert.match(workerRoute, /completed.*needs_input.*blocked/s);
  assert.match(store, /product_intake_requests/);
  assert.match(store, /evidence_url/);
  assert.match(store, /owner_notes/);
  assert.match(store, /nenhuma publicação está autorizada/);
  assert.doesNotMatch(`${ownerRoute}\n${workerRoute}\n${store}`, /console\.(log|error)/);
});

test("research missions stay bounded, read-only and separated from publication", async () => {
  const client = await import("node:fs/promises").then((fs) => fs.readFile(new URL("../app/components/DashboardClient.tsx", import.meta.url), "utf8"));
  const ownerRoute = await import("node:fs/promises").then((fs) => fs.readFile(new URL("../app/api/research-missions/route.ts", import.meta.url), "utf8"));
  const workerRoute = await import("node:fs/promises").then((fs) => fs.readFile(new URL("../app/api/intake/product-research/route.ts", import.meta.url), "utf8"));
  const store = await import("node:fs/promises").then((fs) => fs.readFile(new URL("../app/api/research-missions/store.ts", import.meta.url), "utf8"));
  assert.match(client, /Pedir pesquisa aos funcionários/);
  assert.match(client, /Mercado Livre conectado/);
  assert.match(client, /Amazon pendente/);
  assert.match(client, /Link afiliado: confirmar/);
  assert.match(client, /Publicação: bloqueada/);
  assert.match(ownerRoute, /resultLimit.*3.*10/s);
  assert.match(workerRoute, /requireDashboardIntake/);
  assert.match(workerRoute, /review.*needs_input.*blocked/s);
  assert.match(store, /providerStatus: "not_called"/);
  assert.match(store, /publicationStatus: "blocked"/);
  assert.doesNotMatch(`${ownerRoute}\n${workerRoute}\n${store}`, /axios|http:\/\//);
});

test("approved product analysis becomes a comparable zero-cost campaign package", async () => {
  const client = await import("node:fs/promises").then((fs) => fs.readFile(new URL("../app/components/DashboardClient.tsx", import.meta.url), "utf8"));
  const ownerRoute = await import("node:fs/promises").then((fs) => fs.readFile(new URL("../app/api/products/route.ts", import.meta.url), "utf8"));
  const store = await import("node:fs/promises").then((fs) => fs.readFile(new URL("../app/api/products/store.ts", import.meta.url), "utf8"));
  assert.match(client, /Preparar pacote sem gasto/);
  assert.match(client, /Pacotes preparados/);
  assert.match(client, /Custo estimado/);
  assert.match(ownerRoute, /prepare_campaign/);
  assert.match(store, /campaign_package/);
  assert.match(store, /US\$ 0,00 nesta preparação/);
  assert.match(store, /publicationStatus: "blocked"/);
  assert.match(store, /aprovação final do owner/);
  assert.doesNotMatch(`${ownerRoute}\n${store}`, /fetch\(|axios|http:\/\//);
});

test("selected campaign package becomes an organic brief without execution", async () => {
  const client = await import("node:fs/promises").then((fs) => fs.readFile(new URL("../app/components/DashboardClient.tsx", import.meta.url), "utf8"));
  const ownerRoute = await import("node:fs/promises").then((fs) => fs.readFile(new URL("../app/api/products/route.ts", import.meta.url), "utf8"));
  const store = await import("node:fs/promises").then((fs) => fs.readFile(new URL("../app/api/products/store.ts", import.meta.url), "utf8"));
  assert.match(client, /Criar briefing orgânico/);
  assert.match(client, /Provider não chamado · publicação bloqueada/);
  assert.match(ownerRoute, /prepare_organic_brief/);
  assert.match(store, /ready_for_owner_review/);
  assert.match(store, /metricsToCollect/);
  assert.match(store, /providerStatus: "not_called"/);
  assert.match(store, /publicationStatus: "blocked"/);
  assert.doesNotMatch(`${ownerRoute}\n${store}`, /fetch\(|axios|http:\/\//);
});

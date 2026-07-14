import { desc, eq } from "drizzle-orm";
import { getDb } from "../../../db";
import { activityLog, mediaProductionRequests, opportunities, opportunitySources, productionRequests, providerPlanSelections } from "../../../db/schema";

const seedOpportunities = [
  ["gta-radar", "Radar diário de GTA 6 e lançamentos", "Gaming News Desk", "Fase Nova Games", "Notícia", "Monitorar fontes oficiais e produzir somente quando houver novidade com valor editorial.", "pending", "high", 92, 96, "Baixo: exige confirmação da fonte e bloqueio de rumor.", "Aprovar a pauta para roteiro. Publicação continua separada."],
  ["meccha-v3", "Meccha Chameleon 2.6: revisão editorial V3", "Video Department", "Fase Nova Games", "Vídeo curto", "Novo corte aguardando voz aprovada e correção de motion graphics.", "production", "high", 84, 91, "Médio: voz e composição visual ainda não atingiram o padrão editorial.", "Revisar voz, círculo central e entrada das legendas."],
  ["amazon-dualsense", "Controle DualSense Gray Camouflage com desconto", "Product Research", "Achados Baratos BR", "Oferta", "Controle sem fio para PlayStation 5, com imagem limpa. O link afiliado ainda precisa ser validado.", "pending", "medium", 88, 82, "Médio: preço e estoque precisam ser reconfirmados.", "Inserir link afiliado válido e reconfirmar preço."],
  ["meta-connection", "Conexão comercial Meta e Instagram", "Platform Operations", "Achados Baratos BR", "Integração", "Página e Instagram conectados para operação orgânica; anúncios permanecem restritos.", "blocked", "medium", 61, 100, "Alto: conta comercial proibida de anunciar até revisão da Meta.", "Auditar o ativo restrito sem desfazer o vínculo."],
] as const;

const seedSources = [
  { id: "src-gta-rockstar", opportunityId: "gta-radar", label: "Rockstar Games Newswire", url: "https://www.rockstargames.com/newswire", sourceType: "official", publishedAt: null },
  { id: "src-gta-vi", opportunityId: "gta-radar", label: "Página oficial de GTA VI", url: "https://www.rockstargames.com/VI", sourceType: "official", publishedAt: null },
  { id: "src-meccha-steam", opportunityId: "meccha-v3", label: "Notícias oficiais da Steam", url: "https://store.steampowered.com/news/", sourceType: "official", publishedAt: null },
  { id: "src-dualsense-amazon", opportunityId: "amazon-dualsense", label: "Produto monitorado na Amazon Brasil", url: "https://www.amazon.com.br/", sourceType: "marketplace", publishedAt: null },
  { id: "src-meta-help", opportunityId: "meta-connection", label: "Central de Ajuda da Meta para Empresas", url: "https://www.facebook.com/business/help", sourceType: "official", publishedAt: null },
] as const;

export type OpportunityIntake = {
  id: string;
  title: string;
  source: string;
  channel: string;
  category: string;
  summary: string;
  priority: "low" | "medium" | "high";
  score: number;
  confidence: number;
  risk: string;
  nextAction: string;
  updatedAt: string;
  sources: Array<{
    id: string;
    label: string;
    url: string;
    sourceType: "official" | "reporting" | "marketplace" | "signal";
    publishedAt: string | null;
  }>;
};

export async function dashboardState() {
  const db = getDb();
  await ensureSchema();
  const existing = await db.select().from(opportunities).limit(1);
  if (!existing.length) {
    const now = new Date().toISOString();
    await db.insert(opportunities).values(seedOpportunities.map((item) => ({
      id: item[0], title: item[1], source: item[2], channel: item[3], category: item[4], summary: item[5],
      status: item[6], priority: item[7], score: item[8], confidence: item[9], risk: item[10], nextAction: item[11], updatedAt: now,
    })));
    await db.insert(activityLog).values([
      { id: crypto.randomUUID(), label: "Painel inicializado", detail: "Fila operacional sincronizada", tone: "green", createdAt: now },
      { id: crypto.randomUUID(), label: "Modo seguro ativo", detail: "Publicação e gastos exigem aprovação separada", tone: "cyan", createdAt: now },
    ]);
  }
  const existingSource = await db.select().from(opportunitySources).limit(1);
  if (!existingSource.length) {
    await db.insert(opportunitySources).values(seedSources.map((source) => ({ ...source })));
  }
  const items = await db.select().from(opportunities).orderBy(desc(opportunities.score));
  const sources = await db.select().from(opportunitySources);
  const activity = await db.select().from(activityLog).orderBy(desc(activityLog.createdAt)).limit(8);
  const productions = await db.select().from(productionRequests).orderBy(desc(productionRequests.updatedAt));
  const media = await db.select().from(mediaProductionRequests).orderBy(desc(mediaProductionRequests.updatedAt));
  const providerPlans = await db.select().from(providerPlanSelections).orderBy(desc(providerPlanSelections.updatedAt));
  return shape(items, sources, activity, productions, media, providerPlans);
}

type ProviderPlanId = "local_free" | "hybrid_quality";

export async function selectProviderPlan(id: string, planId: ProviderPlanId) {
  const db = getDb();
  await ensureSchema();
  const media = await db.select().from(mediaProductionRequests).where(eq(mediaProductionRequests.opportunityId, id)).limit(1);
  const script = await db.select().from(productionRequests).where(eq(productionRequests.opportunityId, id)).limit(1);
  if (!media[0] || media[0].status !== "review" || !script[0] || script[0].status !== "media_review") {
    throw new Error("Provider plans require reviewed media pre-production");
  }
  const quote = buildProviderPlans(script[0].script).find((plan) => plan.planId === planId);
  if (!quote) throw new Error("Provider plan is not available");
  const now = new Date().toISOString();
  const values = {
    id: `provider-plan-${id}`, opportunityId: id, planId, quoteSnapshot: JSON.stringify(quote),
    estimatedCostUsd: Math.round(quote.estimatedCostUsd * 100), pricingComplete: quote.completePrice ? 1 : 0,
    executionStatus: "blocked", ownerApprovedExecution: 0, createdAt: now, updatedAt: now,
  };
  await db.insert(providerPlanSelections).values(values).onConflictDoUpdate({
    target: providerPlanSelections.opportunityId,
    set: { planId, quoteSnapshot: values.quoteSnapshot, estimatedCostUsd: values.estimatedCostUsd, pricingComplete: values.pricingComplete, executionStatus: "blocked", ownerApprovedExecution: 0, updatedAt: now },
  });
  await db.update(mediaProductionRequests).set({ providerStatus: "planned_not_called", updatedAt: now }).where(eq(mediaProductionRequests.opportunityId, id));
  await db.insert(activityLog).values({ id: crypto.randomUUID(), label: "Plano de providers selecionado", detail: `${id} · ${quote.displayName} · execução bloqueada`, tone: "cyan", createdAt: now });
  return dashboardState();
}

export async function updateOpportunity(id: string, action: "approve" | "reject" | "discard" | "approve_media") {
  const db = getDb();
  await ensureSchema();
  const existing = await db.select().from(opportunities).where(eq(opportunities.id, id)).limit(1);
  if (!existing[0]) throw new Error("Opportunity was not found");
  if (action === "approve_media") {
    if (existing[0].status !== "review") throw new Error("Only reviewed scripts can enter media pre-production");
    const title = existing[0].title.toLocaleLowerCase("pt-BR");
    const summary = existing[0].summary.toLocaleLowerCase("pt-BR");
    if (title.startsWith("radar diário") || (summary.includes("monitorar fontes") && summary.includes("quando houver novidade"))) {
      throw new Error("Monitoring routines require a concrete news item before media pre-production");
    }
    const script = await db.select().from(productionRequests).where(eq(productionRequests.opportunityId, id)).limit(1);
    if (!script[0] || script[0].status !== "review") throw new Error("Reviewed script was not found");
    const now = new Date().toISOString();
    const values = {
      id: `media-${id}`, opportunityId: id, status: "queued", mode: "MOCK", departments: "{}",
      reviewNotes: "Aguardando Audio, Image e Video Departments prepararem os planos técnicos.",
      qualityPassed: 0, providerStatus: "not_called", finalAssetStatus: "not_generated",
      publicationStatus: "blocked", createdAt: now, updatedAt: now,
    };
    await db.insert(mediaProductionRequests).values(values).onConflictDoUpdate({
      target: mediaProductionRequests.opportunityId,
      set: { status: "queued", departments: "{}", reviewNotes: values.reviewNotes, qualityPassed: 0, updatedAt: now },
    });
    await db.update(productionRequests).set({ status: "media_queued", updatedAt: now }).where(eq(productionRequests.opportunityId, id));
    await db.update(opportunities).set({ status: "production", nextAction: "Aguardar a pré-produção MOCK e revisar os planos de áudio, imagem e vídeo.", updatedAt: now }).where(eq(opportunities.id, id));
    await db.insert(activityLog).values({ id: crypto.randomUUID(), label: "Pré-produção autorizada", detail: `${id} · MOCK · providers e publicação bloqueados`, tone: "cyan", createdAt: now });
    return dashboardState();
  }
  if (action === "discard") {
    if (existing[0].status !== "review") throw new Error("Only review drafts can be discarded");
    const now = new Date().toISOString();
    await db.update(opportunities).set({ status: "blocked", nextAction: "Rascunho descartado pelo owner; nenhuma publicação foi realizada.", updatedAt: now }).where(eq(opportunities.id, id));
    await db.update(productionRequests).set({ status: "failed", reviewNotes: "Rascunho descartado pelo owner.", publicationStatus: "blocked", updatedAt: now }).where(eq(productionRequests.opportunityId, id));
    await db.insert(activityLog).values({ id: crypto.randomUUID(), label: "Rascunho descartado", detail: `${id} · publicação bloqueada`, tone: "red", createdAt: now });
    return dashboardState();
  }
  if (existing[0].status !== "pending") throw new Error("Only pending opportunities can receive a decision");
  const status = action === "approve" ? "approved" : "blocked";
  const now = new Date().toISOString();
  await db.update(opportunities).set({
    status,
    nextAction: action === "approve"
      ? "Aguardar o funcionário preparar o rascunho em modo MOCK. Depois, revisar o material no painel."
      : "Oportunidade encerrada pelo owner.",
    updatedAt: now,
  }).where(eq(opportunities.id, id));
  if (action === "approve") {
    const productionId = `production-${id}`;
    const values = {
      id: productionId,
      opportunityId: id,
      status: "queued",
      mode: "MOCK",
      hook: "",
      script: "",
      callToAction: "",
      assetPlan: "[]",
      reviewNotes: "Aguardando o Script Department preparar o primeiro rascunho.",
      publicationStatus: "blocked",
      createdAt: now,
      updatedAt: now,
    };
    await db.insert(productionRequests).values(values).onConflictDoUpdate({
      target: productionRequests.opportunityId,
      set: { status: "queued", mode: "MOCK", reviewNotes: values.reviewNotes, publicationStatus: "blocked", updatedAt: now },
    });
  }
  await db.insert(activityLog).values({
    id: crypto.randomUUID(),
    label: action === "approve" ? "Produção colocada na fila" : "Oportunidade rejeitada",
    detail: `${id} · modo MOCK · publicação bloqueada`,
    tone: action === "approve" ? "green" : "red",
    createdAt: now,
  });
  return dashboardState();
}

export type ProductionWorkerResult = {
  opportunityId: string;
  status: "review" | "failed";
  hook: string;
  script: string;
  callToAction: string;
  assetPlan: string[];
  reviewNotes: string;
};

export async function productionWorkerQueue(limit = 10) {
  const db = getDb();
  await ensureSchema();
  const runs = await db.select().from(productionRequests)
    .where(eq(productionRequests.status, "queued"))
    .orderBy(productionRequests.createdAt)
    .limit(Math.max(1, Math.min(10, limit)));
  const items = await db.select().from(opportunities);
  const sources = await db.select().from(opportunitySources);
  return {
    items: runs.map((run) => {
      const opportunity = items.find((item) => item.id === run.opportunityId);
      return {
        id: run.id,
        opportunityId: run.opportunityId,
        title: opportunity?.title ?? "",
        summary: opportunity?.summary ?? "",
        channel: opportunity?.channel ?? "",
        category: opportunity?.category ?? "",
        sources: sources.filter((source) => source.opportunityId === run.opportunityId).map((source) => ({
          label: source.label,
          url: source.url,
          sourceType: source.sourceType,
        })),
        mode: "MOCK",
      };
    }).filter((item) => item.title),
  };
}

export async function applyProductionWorkerResult(input: ProductionWorkerResult) {
  const db = getDb();
  await ensureSchema();
  const existing = await db.select().from(productionRequests).where(eq(productionRequests.opportunityId, input.opportunityId)).limit(1);
  if (!existing[0] || existing[0].status !== "queued") throw new Error("Queued production request was not found");
  const now = new Date().toISOString();
  await db.update(productionRequests).set({
    status: input.status,
    hook: input.hook,
    script: input.script,
    callToAction: input.callToAction,
    assetPlan: JSON.stringify(input.assetPlan),
    reviewNotes: input.reviewNotes,
    publicationStatus: "blocked",
    updatedAt: now,
  }).where(eq(productionRequests.opportunityId, input.opportunityId));
  await db.update(opportunities).set({
    status: input.status === "review" ? "review" : "blocked",
    nextAction: input.status === "review"
      ? "Revisar o rascunho. Áudio, vídeo final, gasto e publicação continuam bloqueados."
      : "Corrigir a falha do rascunho antes de tentar novamente.",
    updatedAt: now,
  }).where(eq(opportunities.id, input.opportunityId));
  await db.insert(activityLog).values({
    id: crypto.randomUUID(),
    label: input.status === "review" ? "Rascunho pronto para revisão" : "Produção bloqueada",
    detail: `${input.opportunityId} · publicação bloqueada`,
    tone: input.status === "review" ? "cyan" : "red",
    createdAt: now,
  });
  return dashboardState();
}

export type MediaProductionWorkerResult = {
  opportunityId: string;
  status: "media_review" | "failed";
  reviewNotes: string;
  departments: Record<string, { label: string; status: string; summary: string; qualityPassed: boolean }>;
  qualityPassed?: boolean;
  publicationStatus?: "blocked";
  providerStatus?: "not_called";
  finalAssetStatus?: "not_generated";
};

export async function mediaProductionWorkerQueue(limit = 10) {
  const db = getDb();
  await ensureSchema();
  const media = await db.select().from(mediaProductionRequests).where(eq(mediaProductionRequests.status, "queued")).orderBy(mediaProductionRequests.createdAt).limit(Math.max(1, Math.min(10, limit)));
  const scripts = await db.select().from(productionRequests);
  const items = await db.select().from(opportunities);
  const sources = await db.select().from(opportunitySources);
  return { items: media.map((request) => {
    const script = scripts.find((run) => run.opportunityId === request.opportunityId);
    const opportunity = items.find((item) => item.id === request.opportunityId);
    let assetPlan: string[] = [];
    try { assetPlan = JSON.parse(script?.assetPlan ?? "[]") as string[]; } catch { assetPlan = []; }
    return {
      opportunityId: request.opportunityId, title: opportunity?.title ?? "", channel: opportunity?.channel ?? "", category: opportunity?.category ?? "",
      hook: script?.hook ?? "", script: script?.script ?? "", callToAction: script?.callToAction ?? "", assetPlan,
      sources: sources.filter((source) => source.opportunityId === request.opportunityId).map((source) => ({ label: source.label, url: source.url, sourceType: source.sourceType })),
      mode: "MOCK",
    };
  }).filter((item) => item.title && item.hook && item.script) };
}

export async function applyMediaProductionWorkerResult(input: MediaProductionWorkerResult) {
  const db = getDb();
  await ensureSchema();
  const existing = await db.select().from(mediaProductionRequests).where(eq(mediaProductionRequests.opportunityId, input.opportunityId)).limit(1);
  if (!existing[0] || existing[0].status !== "queued") throw new Error("Queued media request was not found");
  const now = new Date().toISOString();
  const ready = input.status === "media_review";
  await db.update(mediaProductionRequests).set({
    status: ready ? "review" : "failed", departments: JSON.stringify(input.departments), reviewNotes: input.reviewNotes,
    qualityPassed: input.qualityPassed ? 1 : 0, providerStatus: "not_called", finalAssetStatus: "not_generated", publicationStatus: "blocked", updatedAt: now,
  }).where(eq(mediaProductionRequests.opportunityId, input.opportunityId));
  await db.update(productionRequests).set({ status: ready ? "media_review" : "failed", updatedAt: now }).where(eq(productionRequests.opportunityId, input.opportunityId));
  await db.update(opportunities).set({
    status: ready ? "review" : "blocked",
    nextAction: ready ? "Revisar os planos técnicos. Provider real, arquivo final e publicação continuam bloqueados." : "Corrigir a falha da pré-produção antes de avançar.", updatedAt: now,
  }).where(eq(opportunities.id, input.opportunityId));
  await db.insert(activityLog).values({ id: crypto.randomUUID(), label: ready ? "Pré-produção pronta para revisão" : "Pré-produção bloqueada", detail: `${input.opportunityId} · nenhum provider chamado`, tone: ready ? "green" : "red", createdAt: now });
  return dashboardState();
}

export async function upsertOpportunity(input: OpportunityIntake) {
  const db = getDb();
  await ensureSchema();
  const existing = await db.select().from(opportunities).where(eq(opportunities.id, input.id)).limit(1);
  const values = {
    id: input.id,
    title: input.title,
    source: input.source,
    channel: input.channel,
    category: input.category,
    summary: input.summary,
    status: existing[0]?.status ?? "pending",
    priority: input.priority,
    score: input.score,
    confidence: input.confidence,
    risk: input.risk,
    nextAction: input.nextAction,
    updatedAt: input.updatedAt,
  };
  await db.insert(opportunities).values(values).onConflictDoUpdate({
    target: opportunities.id,
    set: values,
  });
  await db.delete(opportunitySources).where(eq(opportunitySources.opportunityId, input.id));
  if (input.sources.length) {
    await db.insert(opportunitySources).values(input.sources.map((source) => ({
      ...source,
      opportunityId: input.id,
    })));
  }
  if (!existing.length) {
    await db.insert(activityLog).values({
      id: crypto.randomUUID(),
      label: "Radar sincronizado",
      detail: `${input.title} · aguardando decisão`,
      tone: "cyan",
      createdAt: new Date().toISOString(),
    });
  }
  return dashboardState();
}

async function ensureSchema() {
  const { env } = await import("cloudflare:workers");
  const d1 = env.DB;
  await d1.batch([
    d1.prepare("CREATE TABLE IF NOT EXISTS opportunities (id TEXT PRIMARY KEY, title TEXT NOT NULL, source TEXT NOT NULL, channel TEXT NOT NULL, category TEXT NOT NULL, summary TEXT NOT NULL, status TEXT NOT NULL, priority TEXT NOT NULL, score INTEGER NOT NULL, confidence INTEGER NOT NULL, risk TEXT NOT NULL, next_action TEXT NOT NULL, updated_at TEXT NOT NULL)"),
    d1.prepare("CREATE TABLE IF NOT EXISTS activity_log (id TEXT PRIMARY KEY, label TEXT NOT NULL, detail TEXT NOT NULL, tone TEXT NOT NULL, created_at TEXT NOT NULL)"),
    d1.prepare("CREATE TABLE IF NOT EXISTS opportunity_sources (id TEXT PRIMARY KEY, opportunity_id TEXT NOT NULL, label TEXT NOT NULL, url TEXT NOT NULL, source_type TEXT NOT NULL, published_at TEXT)"),
    d1.prepare("CREATE TABLE IF NOT EXISTS production_requests (id TEXT PRIMARY KEY, opportunity_id TEXT NOT NULL UNIQUE, status TEXT NOT NULL, mode TEXT NOT NULL, hook TEXT NOT NULL, script TEXT NOT NULL, call_to_action TEXT NOT NULL, asset_plan TEXT NOT NULL, review_notes TEXT NOT NULL, publication_status TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL)"),
    d1.prepare("CREATE TABLE IF NOT EXISTS media_production_requests (id TEXT PRIMARY KEY, opportunity_id TEXT NOT NULL UNIQUE, status TEXT NOT NULL, mode TEXT NOT NULL, departments TEXT NOT NULL, review_notes TEXT NOT NULL, quality_passed INTEGER NOT NULL, provider_status TEXT NOT NULL, final_asset_status TEXT NOT NULL, publication_status TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL)"),
    d1.prepare("CREATE TABLE IF NOT EXISTS provider_plan_selections (id TEXT PRIMARY KEY, opportunity_id TEXT NOT NULL UNIQUE, plan_id TEXT NOT NULL, quote_snapshot TEXT NOT NULL, estimated_cost_usd_cents INTEGER NOT NULL, pricing_complete INTEGER NOT NULL, execution_status TEXT NOT NULL, owner_approved_execution INTEGER NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL)"),
    d1.prepare("CREATE INDEX IF NOT EXISTS opportunities_status_idx ON opportunities(status)"),
    d1.prepare("CREATE INDEX IF NOT EXISTS activity_created_idx ON activity_log(created_at)"),
    d1.prepare("CREATE INDEX IF NOT EXISTS opportunity_sources_opportunity_idx ON opportunity_sources(opportunity_id)"),
    d1.prepare("CREATE INDEX IF NOT EXISTS production_requests_status_idx ON production_requests(status)"),
    d1.prepare("CREATE INDEX IF NOT EXISTS media_production_requests_status_idx ON media_production_requests(status)"),
    d1.prepare("CREATE INDEX IF NOT EXISTS provider_plan_selections_opportunity_idx ON provider_plan_selections(opportunity_id)"),
  ]);
}

function shape(items: Array<typeof opportunities.$inferSelect>, sources: Array<typeof opportunitySources.$inferSelect>, activity: Array<typeof activityLog.$inferSelect>, productions: Array<typeof productionRequests.$inferSelect>, media: Array<typeof mediaProductionRequests.$inferSelect>, selectedPlans: Array<typeof providerPlanSelections.$inferSelect>) {
  return {
    opportunities: items.map((item) => ({
      ...item,
      updatedAt: relativeTime(item.updatedAt),
      sources: sources.filter((source) => source.opportunityId === item.id).map((source) => ({
        id: source.id,
        label: source.label,
        url: source.url,
        sourceType: source.sourceType,
        publishedAt: source.publishedAt,
      })),
    })),
    productions: productions.map((run) => {
      const opportunity = items.find((item) => item.id === run.opportunityId);
      let assetPlan: string[] = [];
      try { assetPlan = JSON.parse(run.assetPlan) as string[]; } catch { assetPlan = []; }
      const mediaRun = media.find((item) => item.opportunityId === run.opportunityId);
      const selectedPlan = selectedPlans.find((item) => item.opportunityId === run.opportunityId);
      let departments: Record<string, unknown> = {};
      try { departments = JSON.parse(mediaRun?.departments ?? "{}") as Record<string, unknown>; } catch { departments = {}; }
      return {
        id: run.id,
        opportunityId: run.opportunityId,
        title: opportunity?.title ?? "Produção sem oportunidade",
        channel: opportunity?.channel ?? "",
        category: opportunity?.category ?? "",
        status: run.status,
        mode: "MOCK",
        hook: run.hook,
        script: run.script,
        callToAction: run.callToAction,
        assetPlan,
        reviewNotes: run.reviewNotes,
        publicationStatus: "blocked",
        updatedAt: relativeTime(run.updatedAt),
        sources: sources.filter((source) => source.opportunityId === run.opportunityId).map((source) => ({
          id: source.id,
          label: source.label,
          url: source.url,
          sourceType: source.sourceType,
        })),
        media: mediaRun ? {
          status: mediaRun.status, reviewNotes: mediaRun.reviewNotes, qualityPassed: Boolean(mediaRun.qualityPassed),
          providerStatus: selectedPlan ? "planned_not_called" : "not_called", finalAssetStatus: "not_generated", publicationStatus: "blocked", departments,
          providerPlans: buildProviderPlans(run.script),
          selectedProviderPlan: selectedPlan?.planId ?? null,
          providerExecutionStatus: "blocked",
        } : null,
      };
    }),
    metrics: {
      pending: items.filter((item) => item.status === "pending").length,
      inProduction: items.filter((item) => item.status === "approved" || item.status === "production").length,
      ready: items.filter((item) => item.status === "review").length,
      blocked: items.filter((item) => item.status === "blocked").length,
    },
    activity: activity.map((item) => ({ id: item.id, label: item.label, detail: item.detail, tone: item.tone, time: relativeTime(item.createdAt) })),
  };
}

function buildProviderPlans(script: string) {
  const words = script.trim().split(/\s+/).filter(Boolean).length;
  const duration = Math.max(15, Math.min(60, Math.round(words / 2.6)));
  const videoCost = Math.round(duration * 10) / 100;
  const requests = Math.max(1, Math.ceil(duration / 10));
  return [
    {
      planId: "local_free", displayName: "Local gratuito", estimatedDurationSeconds: duration,
      estimatedCostUsd: 0, completePrice: true, executableNow: true,
      items: [
        { department: "audio", provider: "kokoro_local", displayName: "Kokoro local", available: true, estimatedCostUsd: 0, limitation: "Gratuito; pronúncia e emoção exigem revisão." },
        { department: "image", provider: "owned_source_assets", displayName: "Materiais próprios/licenciados", available: true, estimatedCostUsd: 0, limitation: "Usa assets com proveniência; não gera imagem nova." },
        { department: "video", provider: "hyperframes_ffmpeg", displayName: "HyperFrames + FFmpeg", available: true, estimatedCostUsd: 0, limitation: "Composição local; depende da qualidade dos assets." },
      ],
      warning: "Sem custo de API. Gerar arquivos locais continuará exigindo outra aprovação.",
    },
    {
      planId: "hybrid_quality", displayName: "Híbrido de maior qualidade", estimatedDurationSeconds: duration,
      estimatedCostUsd: videoCost, completePrice: false, executableNow: false,
      items: [
        { department: "audio", provider: "elevenlabs", displayName: "ElevenLabs", available: false, estimatedCostUsd: 0, limitation: "Fatura pendente; custo ainda não calculado." },
        { department: "image", provider: "image_provider_pending", displayName: "Provider de imagem a escolher", available: false, estimatedCostUsd: 0, limitation: "Comparação de custo, qualidade e licença pendente." },
        { department: "video", provider: "gemini_omni_flash", displayName: "Gemini Omni Flash", available: false, estimatedCostUsd: videoCost, limitation: `Estimativa oficial de US$ 0,10/s · ${requests} clipe(s) de até 10s.` },
      ],
      warning: "Estimativa parcial: não inclui voz nem imagem. Toda execução paga está bloqueada.",
    },
  ];
}

function relativeTime(value: string) {
  const minutes = Math.max(0, Math.round((Date.now() - new Date(value).getTime()) / 60000));
  if (minutes < 1) return "agora";
  if (minutes < 60) return `há ${minutes} min`;
  const hours = Math.round(minutes / 60);
  return hours < 24 ? `há ${hours} h` : `há ${Math.round(hours / 24)} d`;
}

"use client";

import {
  Activity,
  BadgeDollarSign,
  BookOpenCheck,
  Check,
  ChevronRight,
  CircleAlert,
  Clock3,
  Command,
  Cpu,
  ExternalLink,
  Eye,
  FileSearch,
  History,
  ImageIcon,
  LayoutDashboard,
  Menu,
  Newspaper,
  Palette,
  PackagePlus,
  Radio,
  RefreshCw,
  Search,
  Send,
  Settings2,
  ShoppingBag,
  ShieldCheck,
  Sparkles,
  X,
} from "lucide-react";
import Image from "next/image";
import { useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import type { DashboardPayload, LearningSourceItem, LearningSourcePayload, Opportunity, OpportunityStatus, ProductIntakeItem, ProductIntakePayload, ProductResearchCandidate, ProductResearchMissionItem, ProductResearchMissionPayload, ProductionRequest, TelegramPublication, TelegramPublicationPayload } from "./types";
import { LearningInboxView, type LearningAuditForm, type LearningSourceForm } from "./LearningInboxView";
import styles from "./dashboard.module.css";

type View = "central" | "products" | "learning" | "opportunities" | "production" | "channels" | "activity" | "settings";
type Theme = "operational" | "matrix";
type CategoryFilter = "all" | "Notícia" | "Oferta" | "Vídeo curto" | "Integração";
type ProductFormInput = {
  productUrl: string;
  affiliateUrl: string;
  evidenceUrl: string;
  language: string;
  sourceKind: string;
  ownerNotes: string;
  targetChannel: string;
  trackingLabel: string;
  channelRegistered: boolean;
};
type ResearchMissionFormInput = { goal: string; marketplaces: string[]; category: string; maxPrice: string; timeframe: string; resultLimit: number; targetChannel: string };
type CommercialFormInput = {
  currentPrice: string;
  oldPrice: string;
  commissionConfirmed: boolean;
  channelRegistered: boolean;
  creativeReviewStatus: "official_link_preview" | "custom_creative_approved";
};

const fallback: DashboardPayload = {
  metrics: { pending: 2, inProduction: 1, ready: 0, blocked: 1 },
  productions: [],
  opportunities: [
    {
      id: "gta-radar",
      title: "Radar diário de GTA 6 e lançamentos",
      source: "Gaming News Desk",
      channel: "Fase Nova Games",
      category: "Notícia",
      summary: "Monitorar apenas fontes oficiais e veículos confiáveis. Produzir somente quando houver novidade com valor editorial.",
      status: "pending",
      priority: "high",
      score: 92,
      confidence: 96,
      risk: "Baixo: exige confirmação da fonte e bloqueio de rumor.",
      nextAction: "Aprovar a pauta para roteiro. Publicação continua separada.",
      updatedAt: "há 8 min",
      sources: [
        { id: "src-gta-rockstar", label: "Rockstar Games Newswire", url: "https://www.rockstargames.com/newswire", sourceType: "official" },
        { id: "src-gta-vi", label: "Página oficial de GTA VI", url: "https://www.rockstargames.com/VI", sourceType: "official" },
      ],
    },
    {
      id: "meccha-v3",
      title: "Meccha Chameleon 2.6: revisão editorial V3",
      source: "Video Department",
      channel: "Fase Nova Games",
      category: "Vídeo curto",
      summary: "Novo corte aguardando voz aprovada e correção de motion graphics antes da revisão final.",
      status: "production",
      priority: "high",
      score: 84,
      confidence: 91,
      risk: "Médio: voz e composição visual ainda não atingiram o padrão editorial.",
      nextAction: "Revisar voz, círculo central e entrada das legendas.",
      updatedAt: "há 31 min",
      sources: [{ id: "src-meccha-steam", label: "Notícias oficiais da Steam", url: "https://store.steampowered.com/news/", sourceType: "official" }],
    },
    {
      id: "amazon-dualsense",
      title: "Controle DualSense Gray Camouflage com desconto",
      source: "Product Research",
      channel: "Achados Baratos BR",
      category: "Oferta",
      summary: "Controle sem fio para PlayStation 5, com imagem limpa e bom potencial de clique. O link afiliado ainda precisa ser validado.",
      status: "pending",
      priority: "medium",
      score: 88,
      confidence: 82,
      risk: "Médio: preço e estoque precisam ser reconfirmados antes da postagem.",
      nextAction: "Inserir link afiliado válido e reconfirmar preço.",
      updatedAt: "há 1 h",
      sources: [{ id: "src-dualsense-amazon", label: "Produto monitorado na Amazon Brasil", url: "https://www.amazon.com.br/", sourceType: "marketplace" }],
    },
    {
      id: "meta-connection",
      title: "Conexão comercial Meta e Instagram",
      source: "Platform Operations",
      channel: "Achados Baratos BR",
      category: "Integração",
      summary: "Página e Instagram conectados para operação orgânica. Recursos comerciais completos estão restritos pela Meta.",
      status: "blocked",
      priority: "medium",
      score: 61,
      confidence: 100,
      risk: "Alto: conta comercial proibida de anunciar até revisão da Meta.",
      nextAction: "Auditar o ativo restrito e solicitar análise sem desfazer o vínculo.",
      updatedAt: "ontem",
      sources: [{ id: "src-meta-help", label: "Central de Ajuda da Meta para Empresas", url: "https://www.facebook.com/business/help", sourceType: "official" }],
    },
  ],
  activity: [
    { id: "a1", label: "Instagram conectado", detail: "@achadosbaratosbr2 vinculado à Página", time: "ontem", tone: "green" },
    { id: "a2", label: "Radar diário executado", detail: "Nenhum rumor foi promovido a pauta", time: "09:00", tone: "cyan" },
    { id: "a3", label: "Produção aguardando voz", detail: "Meccha Chameleon mantido em revisão", time: "08:41", tone: "amber" },
  ],
};

const statusLabel: Record<OpportunityStatus, string> = {
  pending: "Aguardando decisão",
  approved: "Na fila de produção",
  production: "Em produção",
  review: "Pronta para revisão",
  blocked: "Bloqueada",
};

const viewMeta: Record<View, { title: string; eyebrow: string; description: string }> = {
  central: { title: "Central de comando", eyebrow: "OPERAÇÃO AO VIVO", description: "O que precisa da sua atenção agora, sem misturar configuração técnica." },
  products: { title: "Produtos", eyebrow: "ENTRADA COMERCIAL", description: "Envie uma página de produto e acompanhe cada validação antes de decidir." },
  learning: { title: "Aprendizado", eyebrow: "INTELIGÊNCIA CONTROLADA", description: "Receba fontes, acompanhe evidências e decida o que merece virar conhecimento da fábrica." },
  opportunities: { title: "Oportunidades", eyebrow: "DECISÃO HUMANA", description: "Insights dos funcionários, evidências e riscos antes de qualquer produção." },
  production: { title: "Produção", eyebrow: "ESTEIRA DA FÁBRICA", description: "Onde cada trabalho está, o que já terminou e o que está impedindo o avanço." },
  channels: { title: "Canais", eyebrow: "DISTRIBUIÇÃO", description: "Marcas, redes e integrações preparadas para receber conteúdo aprovado." },
  activity: { title: "Histórico", eyebrow: "AUDITORIA", description: "Decisões, mudanças e verificações registradas para você poder conferir depois." },
  settings: { title: "Configurações", eyebrow: "CONTROLE DO OWNER", description: "Aparência, providers, orçamento e proteções da operação." },
};

function greetingForHour(hour: number) {
  if (hour < 5) return "Boa madrugada";
  if (hour < 12) return "Bom dia";
  if (hour < 18) return "Boa tarde";
  return "Boa noite";
}

export function DashboardClient({ operator, authenticated }: { operator: string; authenticated: boolean }) {
  const [data, setData] = useState<DashboardPayload>(fallback);
  const [products, setProducts] = useState<ProductIntakeItem[]>([]);
  const [learningSources, setLearningSources] = useState<LearningSourceItem[]>([]);
  const [researchMissions, setResearchMissions] = useState<ProductResearchMissionItem[]>([]);
  const [telegramPublications, setTelegramPublications] = useState<TelegramPublication[]>([]);
  const [view, setView] = useState<View>("central");
  const [theme, setTheme] = useState<Theme>("operational");
  const [selectedId, setSelectedId] = useState(fallback.opportunities[0].id);
  const [filter, setFilter] = useState<OpportunityStatus | "all">("all");
  const [category, setCategory] = useState<CategoryFilter>("all");
  const [query, setQuery] = useState("");
  const [globalQuery, setGlobalQuery] = useState("");
  const [searchOpen, setSearchOpen] = useState(false);
  const [busy, setBusy] = useState<string | null>(null);
  const [notice, setNotice] = useState("");
  const [mobileNav, setMobileNav] = useState(false);
  const [greeting, setGreeting] = useState("Olá");
  const globalSearchInput = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const updateGreeting = () => setGreeting(greetingForHour(new Date().getHours()));
    updateGreeting();
    const timer = window.setInterval(updateGreeting, 60_000);
    return () => window.clearInterval(timer);
  }, []);

  useEffect(() => {
    const themeFrame = window.requestAnimationFrame(() => {
      const savedTheme = window.localStorage.getItem("factory-theme");
      if (savedTheme === "matrix" || savedTheme === "operational") setTheme(savedTheme);
    });
    fetch("/api/dashboard")
      .then((response) => (response.ok ? response.json() : Promise.reject()))
      .then((payload: DashboardPayload) => {
        if (payload.opportunities?.length) {
          setData(payload);
          setSelectedId(payload.opportunities[0].id);
        }
      })
      .catch(() => setNotice("Visualização local ativa. O banco será sincronizado na publicação."));
    fetch("/api/products")
      .then((response) => (response.ok ? response.json() : Promise.reject()))
      .then((payload: ProductIntakePayload) => setProducts(payload.items ?? []))
      .catch(() => undefined);
    fetch("/api/learning-sources")
      .then((response) => (response.ok ? response.json() : Promise.reject()))
      .then((payload: LearningSourcePayload) => setLearningSources(payload.items ?? []))
      .catch(() => undefined);
    fetch("/api/research-missions")
      .then((response) => (response.ok ? response.json() : Promise.reject()))
      .then((payload: ProductResearchMissionPayload) => setResearchMissions(payload.missions ?? []))
      .catch(() => undefined);
    fetch("/api/telegram-publications")
      .then((response) => (response.ok ? response.json() : Promise.reject()))
      .then((payload: TelegramPublicationPayload) => setTelegramPublications(payload.publications ?? []))
      .catch(() => undefined);
    return () => window.cancelAnimationFrame(themeFrame);
  }, []);

  useEffect(() => {
    function closeOnEscape(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setSearchOpen(false);
        setMobileNav(false);
      }
    }
    window.addEventListener("keydown", closeOnEscape);
    return () => window.removeEventListener("keydown", closeOnEscape);
  }, []);

  const visible = useMemo(() => {
    const needle = query.trim().toLowerCase();
    return data.opportunities.filter((item) => {
      const matchesStatus = filter === "all" || item.status === filter;
      const matchesCategory = category === "all" || item.category === category;
      const matchesQuery = !needle || `${item.title} ${item.channel} ${item.source} ${item.category}`.toLowerCase().includes(needle);
      return matchesStatus && matchesCategory && matchesQuery;
    });
  }, [data.opportunities, filter, category, query]);

  const selected = data.opportunities.find((item) => item.id === selectedId) ?? visible[0] ?? data.opportunities[0];
  const pending = data.opportunities.filter((item) => item.status === "pending");

  const globalResults = useMemo(() => {
    const needle = globalQuery.trim().toLowerCase();
    if (!needle) return data.opportunities.slice(0, 3);
    return data.opportunities.filter((item) => `${item.title} ${item.channel} ${item.source} ${item.category}`.toLowerCase().includes(needle));
  }, [data.opportunities, globalQuery]);

  function changeView(next: View) {
    setView(next);
    setMobileNav(false);
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function changeTheme(next: Theme) {
    setTheme(next);
    window.localStorage.setItem("factory-theme", next);
  }

  function openSearch() {
    setSearchOpen(true);
    setGlobalQuery("");
    window.setTimeout(() => globalSearchInput.current?.focus(), 0);
  }

  function openOpportunity(item: Opportunity) {
    setSelectedId(item.id);
    setView("opportunities");
    setSearchOpen(false);
    setMobileNav(false);
  }

  function openMetric(status: OpportunityStatus) {
    setFilter(status);
    setCategory("all");
    setQuery("");
    setView("opportunities");
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  async function synchronize() {
    setBusy("sync");
    try {
      const response = await fetch("/api/dashboard");
      if (!response.ok) throw new Error("Falha ao sincronizar");
      const payload = (await response.json()) as DashboardPayload;
      setData(payload);
      setNotice("Fila sincronizada. Nenhuma produção ou publicação foi iniciada.");
    } catch {
      setNotice("Não foi possível sincronizar agora. A fila visível foi preservada.");
    } finally {
      setBusy(null);
    }
  }

  async function decide(action: "approve" | "reject") {
    if (!selected) return;
    setBusy(action);
    setNotice("");
    const nextStatus: OpportunityStatus = action === "approve" ? "approved" : "blocked";
    try {
      const response = await fetch("/api/actions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id: selected.id, action }),
      });
      if (!response.ok) throw new Error("Falha ao registrar decisão");
      const payload = (await response.json()) as DashboardPayload;
      setData(payload);
      setNotice(action === "approve" ? "Solicitação criada na fila MOCK. Um rascunho voltará para sua revisão; nada foi publicado ou cobrado." : "Pauta rejeitada e retirada da produção.");
    } catch {
      setData((current) => ({
        ...current,
        opportunities: current.opportunities.map((item) => item.id === selected.id ? { ...item, status: nextStatus } : item),
      }));
      setNotice("Decisão aplicada nesta visualização. A persistência online será ativada na publicação.");
    } finally {
      setBusy(null);
    }
  }

  async function discardProduction(id: string) {
    setBusy(`discard-${id}`);
    setNotice("");
    try {
      const response = await fetch("/api/actions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id, action: "discard" }),
      });
      if (!response.ok) throw new Error("Falha ao descartar rascunho");
      setData(await response.json() as DashboardPayload);
      setNotice("Rascunho descartado. Nada foi publicado ou cobrado.");
    } catch {
      setNotice("Não foi possível descartar o rascunho agora.");
    } finally {
      setBusy(null);
    }
  }

  async function approveMediaProduction(id: string) {
    setBusy(`media-${id}`);
    setNotice("");
    try {
      const response = await fetch("/api/actions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id, action: "approve_media" }),
      });
      if (!response.ok) throw new Error("Falha ao autorizar pré-produção");
      setData(await response.json() as DashboardPayload);
      setNotice("Pré-produção MOCK autorizada. Áudio, imagem e vídeo voltarão como planos para revisão; nenhum provider foi chamado.");
    } catch {
      setNotice("Não foi possível autorizar a pré-produção agora.");
    } finally {
      setBusy(null);
    }
  }

  async function selectProviderPlan(id: string, planId: "local_free" | "hybrid_quality") {
    setBusy(`provider-${id}`);
    setNotice("");
    try {
      const response = await fetch("/api/actions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id, action: "select_provider_plan", planId }),
      });
      if (!response.ok) throw new Error("Falha ao guardar o plano de providers");
      setData(await response.json() as DashboardPayload);
      setNotice("Plano de providers guardado. Nenhuma API foi chamada e a geração continua bloqueada.");
    } catch {
      setNotice("Não foi possível guardar o plano de providers agora.");
    } finally {
      setBusy(null);
    }
  }

  async function addProduct(input: ProductFormInput) {
    setBusy("product");
    setNotice("");
    try {
      const response = await fetch("/api/products", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(input),
      });
      const payload = await response.json() as ProductIntakePayload & { error?: string };
      if (!response.ok) throw new Error(payload.error || "Não foi possível adicionar o produto");
      setProducts(payload.items ?? []);
      const dashboardResponse = await fetch("/api/dashboard");
      if (dashboardResponse.ok) setData(await dashboardResponse.json() as DashboardPayload);
      setNotice("Produto recebido. A análise não publica nem altera o link informado.");
      return true;
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "Não foi possível adicionar o produto.");
      return false;
    } finally {
      setBusy(null);
    }
  }

  async function addLearningSource(input: LearningSourceForm) {
    setBusy("learning-source");
    setNotice("");
    try {
      const response = await fetch("/api/learning-sources", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(input),
      });
      const payload = await response.json() as LearningSourcePayload & { error?: string };
      if (!response.ok) throw new Error(payload.error || "Não foi possível registrar a fonte");
      setLearningSources(payload.items ?? []);
      setNotice(input.transcript.trim()
        ? "Fonte e transcrição recebidas. Auditoria, experimento e aprendizado oficial continuam bloqueados."
        : "Fonte registrada. Ela ficará aguardando transcrição; nenhuma API foi chamada.");
      return true;
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "Não foi possível registrar a fonte.");
      return false;
    } finally {
      setBusy(null);
    }
  }

  async function auditLearningSource(sourceId: string, input: LearningAuditForm) {
    setBusy(`learning-audit-${sourceId}`);
    setNotice("");
    try {
      const response = await fetch("/api/learning-sources", {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: "audit_transcript", sourceId, ...input }),
      });
      const payload = await response.json() as LearningSourcePayload & { error?: string };
      if (!response.ok) throw new Error(payload.error || "Não foi possível registrar a evidência");
      setLearningSources(payload.items ?? []);
      setNotice("Evidência vinculada à transcrição. Veredito parcial: experimento, memória e publicação continuam bloqueados.");
      return true;
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "Não foi possível registrar a evidência.");
      return false;
    } finally {
      setBusy(null);
    }
  }

  async function addResearchMission(input: ResearchMissionFormInput) {
    setBusy("research-mission");
    setNotice("");
    try {
      const response = await fetch("/api/research-missions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...input, maxPrice: input.maxPrice ? Number(input.maxPrice) : null }),
      });
      const payload = await response.json() as ProductResearchMissionPayload & { error?: string };
      if (!response.ok) throw new Error(payload.error || "Não foi possível criar a pesquisa");
      setResearchMissions(payload.missions ?? []);
      setNotice("Missão registrada. A coleta será somente leitura e voltará como shortlist; publicação e gastos continuam bloqueados.");
      return true;
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "Não foi possível criar a pesquisa.");
      return false;
    } finally {
      setBusy(null);
    }
  }

  async function archiveResearchMission(missionId: string) {
    setBusy(`archive-research-${missionId}`);
    setNotice("");
    try {
      const response = await fetch("/api/research-missions", {
        method: "DELETE",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ missionId }),
      });
      const payload = await response.json() as ProductResearchMissionPayload & { error?: string };
      if (!response.ok) throw new Error(payload.error || "Não foi possível arquivar a pesquisa");
      setResearchMissions(payload.missions ?? []);
      setNotice("Pesquisa de teste arquivada. Os dados foram preservados e ela saiu da sua tela.");
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "Não foi possível arquivar a pesquisa.");
    } finally {
      setBusy(null);
    }
  }

  async function prepareCampaign(productId: string) {
    setBusy(`campaign-${productId}`);
    setNotice("");
    try {
      const response = await fetch("/api/products", {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: "prepare_campaign", productId }),
      });
      const payload = await response.json() as ProductIntakePayload & { error?: string };
      if (!response.ok) throw new Error(payload.error || "Não foi possível preparar o pacote");
      setProducts(payload.items ?? []);
      setNotice("Pacote comparável preparado com custo zero. Publicação, anúncios e providers continuam bloqueados.");
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "Não foi possível preparar o pacote.");
    } finally {
      setBusy(null);
    }
  }

  async function retryProductAnalysis(productId: string) {
    setBusy(`retry-${productId}`);
    setNotice("");
    try {
      const response = await fetch("/api/products", {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: "retry_analysis", productId }),
      });
      const payload = await response.json() as ProductIntakePayload & { error?: string };
      if (!response.ok) throw new Error(payload.error || "Não foi possível reenviar a coleta");
      setProducts(payload.items ?? []);
      setNotice("Produto recolocado na coleta. O worker buscará apenas a página enviada; publicação continua bloqueada.");
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "Não foi possível reenviar a coleta.");
    } finally {
      setBusy(null);
    }
  }

  async function prepareOrganicBrief(productId: string) {
    setBusy(`brief-${productId}`);
    setNotice("");
    try {
      const response = await fetch("/api/products", {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: "prepare_organic_brief", productId }),
      });
      const payload = await response.json() as ProductIntakePayload & { error?: string };
      if (!response.ok) throw new Error(payload.error || "Não foi possível criar o briefing");
      setProducts(payload.items ?? []);
      setNotice("Briefing orgânico criado para sua revisão. Providers, gastos e publicação continuam bloqueados.");
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "Não foi possível criar o briefing.");
    } finally {
      setBusy(null);
    }
  }

  async function completeCommercial(productId: string, input: CommercialFormInput) {
    setBusy(`commercial-${productId}`);
    setNotice("");
    try {
      const response = await fetch("/api/products", {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          action: "complete_commercial",
          productId,
          currentPrice: input.currentPrice,
          oldPrice: input.oldPrice || null,
          commissionConfirmed: input.commissionConfirmed,
          channelRegistered: input.channelRegistered,
          creativeReviewStatus: input.creativeReviewStatus,
        }),
      });
      const payload = await response.json() as ProductIntakePayload & { error?: string };
      if (!response.ok) throw new Error(payload.error || "Não foi possível confirmar os dados comerciais");
      setProducts(payload.items ?? []);
      setNotice("Dados comerciais confirmados e prévia do Telegram atualizada. Nada foi publicado.");
      return true;
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "Não foi possível confirmar os dados comerciais.");
      return false;
    } finally {
      setBusy(null);
    }
  }

  async function queueTelegramPublication(productId: string) {
    setBusy(`telegram-${productId}`);
    setNotice("");
    try {
      const response = await fetch("/api/telegram-publications", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: "prepare_product", productId, confirmation: "PREPARAR CANDIDATO" }),
      });
      const payload = await response.json() as TelegramPublicationPayload & { error?: string };
      if (!response.ok) throw new Error(payload.error || "Não foi possível preparar o candidato");
      setTelegramPublications(payload.publications ?? []);
      setNotice("Candidato preparado para sua aprovação. Nada foi publicado ou colocado na fila de envio.");
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "Não foi possível preparar o candidato.");
    } finally {
      setBusy(null);
    }
  }

  async function prepareEditorialTelegramCandidate() {
    setBusy("telegram-editorial"); setNotice("");
    try {
      const response = await fetch("/api/telegram-publications", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ action: "prepare_editorial", confirmation: "PREPARAR CANDIDATO" }) });
      const payload = await response.json() as TelegramPublicationPayload & { error?: string };
      if (!response.ok) throw new Error(payload.error || "Não foi possível preparar o candidato editorial");
      setTelegramPublications(payload.publications ?? []);
      setNotice("Candidato editorial preparado. PUBLICAÇÃO: NÃO EXECUTADA.");
    } catch (error) { setNotice(error instanceof Error ? error.message : "Não foi possível preparar o candidato editorial."); }
    finally { setBusy(null); }
  }

  async function approveTelegramPublication(requestId: string) {
    setBusy(`telegram-approve-${requestId}`); setNotice("");
    try {
      const response = await fetch("/api/telegram-publications", { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ action: "approve", requestId, confirmation: "APROVAR PUBLICACAO TELEGRAM" }) });
      const payload = await response.json() as TelegramPublicationPayload & { error?: string };
      if (!response.ok) throw new Error(payload.error || "Não foi possível aprovar o candidato");
      setTelegramPublications(payload.publications ?? []);
      setNotice("Candidato aprovado e colocado na fila local. Nenhum envio foi executado.");
    } catch (error) { setNotice(error instanceof Error ? error.message : "Não foi possível aprovar o candidato."); }
    finally { setBusy(null); }
  }

  async function retryTelegramPublication(requestId: string) {
    setBusy(`telegram-retry-${requestId}`);
    setNotice("");
    try {
      const response = await fetch("/api/telegram-publications", {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ requestId }),
      });
      const payload = await response.json() as TelegramPublicationPayload & { error?: string };
      if (!response.ok) throw new Error(payload.error || "Não foi possível reenviar para a fila");
      setTelegramPublications(payload.publications ?? []);
      setNotice("Publicação devolvida à fila. Não haverá duplicação de uma mensagem já enviada.");
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "Não foi possível reenviar para a fila.");
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className={styles.shell} data-theme={theme}>
      {theme === "matrix" && <div className={styles.matrixRain} aria-hidden="true">{Array.from({ length: 14 }, (_, index) => <span key={index}>0100110101101001010011010010110100101101</span>)}</div>}
      {mobileNav && <button className={styles.navBackdrop} aria-label="Fechar menu" onClick={() => setMobileNav(false)} />}

      <aside className={`${styles.sidebar} ${mobileNav ? styles.sidebarOpen : ""}`}>
        <div className={styles.brand}>
          <span className={styles.brandMark}><Command size={20} /></span>
          <span>AI CONTENT<br /><b>FACTORY</b></span>
          <button className={styles.mobileClose} aria-label="Fechar menu" onClick={() => setMobileNav(false)}><X size={18} /></button>
        </div>
        <nav aria-label="Navegação principal">
          <NavButton active={view === "central"} icon={<LayoutDashboard />} label="Central" onClick={() => changeView("central")} />
          <NavButton active={view === "products"} icon={<ShoppingBag />} label="Produtos" badge={products.length} onClick={() => changeView("products")} />
          <NavButton active={view === "learning"} icon={<BookOpenCheck />} label="Aprendizado" badge={learningSources.length} onClick={() => changeView("learning")} />
          <NavButton active={view === "opportunities"} icon={<FileSearch />} label="Oportunidades" badge={data.opportunities.length} onClick={() => changeView("opportunities")} />
          <NavButton active={view === "production"} icon={<Cpu />} label="Produção" badge={data.productions.length} onClick={() => changeView("production")} />
          <NavButton active={view === "channels"} icon={<Radio />} label="Canais" onClick={() => changeView("channels")} />
          <NavButton active={view === "activity"} icon={<History />} label="Histórico" onClick={() => changeView("activity")} />
        </nav>
        <button className={styles.sideStatus} onClick={() => changeView("activity")} title="Verificações automáticas que protegem a arquitetura da fábrica">
          <span><i className={styles.pulse} /> Operação segura</span>
          <strong>Fábrica estável</strong>
          <small>119 demonstrações técnicas aprovadas</small>
        </button>
        <NavButton className={styles.settingsButton} active={view === "settings"} icon={<Settings2 />} label="Configurações" onClick={() => changeView("settings")} />
      </aside>

      <main className={styles.main}>
        <header className={styles.header}>
          <button className={styles.mobileMenu} aria-label="Abrir menu" onClick={() => setMobileNav(true)}><Menu size={20} /></button>
          <div>
            <p className={styles.eyebrow}>{viewMeta[view].eyebrow}</p>
            <h1>{view === "central" ? `${greeting}, ${operator.split(" ")[0]}.` : viewMeta[view].title}</h1>
            <p>{viewMeta[view].description}</p>
          </div>
          <div className={styles.headerTools}>
            <button aria-label="Abrir busca global" onClick={openSearch}><Search size={18} /></button>
            <div className={styles.operatorBadge} title={authenticated ? "Sessão autenticada" : "Visualização local"}>
              <ShieldCheck size={17} /> {authenticated ? "Acesso protegido" : "Modo local"}
            </div>
          </div>
        </header>

        {notice && <div className={styles.notice} role="status"><CircleAlert size={16} /> {notice}<button aria-label="Fechar aviso" onClick={() => setNotice("")}><X size={15} /></button></div>}

        {view === "central" && <CentralView data={data} pending={pending} onOpenOpportunity={openOpportunity} onMetric={openMetric} onView={changeView} />}
        {view === "products" && <ProductsView items={products} missions={researchMissions} publications={telegramPublications} busy={busy} onSubmit={addProduct} onSubmitMission={addResearchMission} onArchiveMission={archiveResearchMission} onPrepareCampaign={prepareCampaign} onPrepareBrief={prepareOrganicBrief} onRetryAnalysis={retryProductAnalysis} onCompleteCommercial={completeCommercial} onQueueTelegram={queueTelegramPublication} onApproveTelegram={approveTelegramPublication} onRetryTelegram={retryTelegramPublication} />}
          {view === "learning" && <LearningInboxView items={learningSources} busy={busy} onSubmit={addLearningSource} onAudit={auditLearningSource} />}
        {view === "opportunities" && <OpportunitiesView
          visible={visible}
          selected={selected}
          filter={filter}
          category={category}
          query={query}
          busy={busy}
          onFilter={setFilter}
          onCategory={setCategory}
          onQuery={setQuery}
          onSelect={setSelectedId}
          onSynchronize={synchronize}
          onDecide={decide}
        />}
        {view === "production" && <ProductionView productions={data.productions} busy={busy} onDiscard={discardProduction} onApproveMedia={approveMediaProduction} onSelectProviderPlan={selectProviderPlan} />}
        {view === "channels" && <ChannelsView publications={telegramPublications} busy={busy} onPrepareEditorial={prepareEditorialTelegramCandidate} onApprove={approveTelegramPublication} onRetry={retryTelegramPublication} />}
        {view === "activity" && <ActivityView activity={data.activity} />}
        {view === "settings" && <SettingsView theme={theme} onTheme={changeTheme} />}
      </main>

      {searchOpen && <div className={styles.searchOverlay} role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) setSearchOpen(false); }}>
        <section className={styles.commandPalette} role="dialog" aria-modal="true" aria-label="Busca global da fábrica">
          <div className={styles.commandSearch}><Search size={19} /><input ref={globalSearchInput} value={globalQuery} onChange={(event) => setGlobalQuery(event.target.value)} placeholder="Buscar oportunidade, canal ou funcionário" /><button aria-label="Fechar busca" onClick={() => setSearchOpen(false)}><X size={18} /></button></div>
          {!globalQuery && <div className={styles.quickSearches}>
            <button onClick={() => { changeView("opportunities"); setSearchOpen(false); }}><FileSearch size={16} /> Ver todas as oportunidades</button>
            <button onClick={() => { changeView("products"); setSearchOpen(false); }}><PackagePlus size={16} /> Adicionar produto</button>
            <button onClick={() => { changeView("production"); setSearchOpen(false); }}><Cpu size={16} /> Acompanhar produções</button>
            <button onClick={() => { changeView("settings"); setSearchOpen(false); }}><Palette size={16} /> Escolher tema</button>
          </div>}
          <div className={styles.searchResults}>
            <p>{globalQuery ? "Resultados" : "Oportunidades recentes"}</p>
            {globalResults.map((item) => <button key={item.id} onClick={() => openOpportunity(item)}><span><strong>{item.title}</strong><small>{item.source} · {item.channel}</small></span><ChevronRight size={17} /></button>)}
            {!globalResults.length && <div className={styles.empty}>Nenhum resultado encontrado.</div>}
          </div>
        </section>
      </div>}
    </div>
  );
}

function CentralView({ data, pending, onOpenOpportunity, onMetric, onView }: { data: DashboardPayload; pending: Opportunity[]; onOpenOpportunity: (item: Opportunity) => void; onMetric: (status: OpportunityStatus) => void; onView: (view: View) => void }) {
  return <>
    <section className={styles.metrics} aria-label="Resumo da operação">
      <Metric label="Aguardando decisão" value={data.metrics.pending} detail="precisam de você" icon={<Clock3 />} tone="green" onClick={() => onMetric("pending")} />
      <Metric label="Fila e produção" value={data.metrics.inProduction} detail="aprovadas ou em trabalho" icon={<Cpu />} tone="cyan" onClick={() => onView("production")} />
      <Metric label="Prontas para revisão" value={data.metrics.ready} detail="ainda não publicadas" icon={<Eye />} tone="amber" onClick={() => onMetric("review")} />
      <Metric label="Bloqueios" value={data.metrics.blocked} detail="exigem correção" icon={<CircleAlert />} tone="red" onClick={() => onMetric("blocked")} />
    </section>
    <section className={styles.centralGrid}>
      <div className={styles.attentionPanel}>
        <SectionHead kicker="PRIORIDADE" title="O que precisa de você" action={<button className={styles.textButton} onClick={() => onView("opportunities")}>Abrir fila <ChevronRight size={15} /></button>} />
        {pending.length ? pending.slice(0, 3).map((item) => <button className={styles.attentionRow} key={item.id} onClick={() => onOpenOpportunity(item)}><span className={`${styles.priorityBar} ${item.priority === "high" ? styles.redBg : styles.amberBg}`} /><span><strong>{item.title}</strong><small>{item.source} · Score {item.score}</small></span><Status status={item.status} /><ChevronRight size={18} /></button>) : <div className={styles.empty}>Nenhuma decisão pendente.</div>}
      </div>
      <div className={styles.todayPanel}>
        <SectionHead kicker="HOJE" title="Fábrica em movimento" />
        <button className={styles.todayAction} onClick={() => onView("products")}><ShoppingBag size={20} /><span><strong>Entrada de produtos</strong><small>Enviar URL para pesquisa e revisão</small></span><ChevronRight size={17} /></button>
        <button className={styles.todayAction} onClick={() => onView("channels")}><Radio size={20} /><span><strong>2 marcas em preparação</strong><small>Fase Nova Games e Achados Baratos BR</small></span><ChevronRight size={17} /></button>
        <button className={styles.todayAction} onClick={() => onView("activity")}><Activity size={20} /><span><strong>Modo seguro ativo</strong><small>Publicação e gastos continuam separados</small></span><ChevronRight size={17} /></button>
      </div>
    </section>
  </>;
}

function ProductsView({ items, missions, publications, busy, onSubmit, onSubmitMission, onArchiveMission, onPrepareCampaign, onPrepareBrief, onRetryAnalysis, onCompleteCommercial, onQueueTelegram, onApproveTelegram, onRetryTelegram }: { items: ProductIntakeItem[]; missions: ProductResearchMissionItem[]; publications: TelegramPublication[]; busy: string | null; onSubmit: (input: ProductFormInput) => Promise<boolean>; onSubmitMission: (input: ResearchMissionFormInput) => Promise<boolean>; onArchiveMission: (missionId: string) => void; onPrepareCampaign: (productId: string) => void; onPrepareBrief: (productId: string) => void; onRetryAnalysis: (productId: string) => void; onCompleteCommercial: (productId: string, input: CommercialFormInput) => Promise<boolean>; onQueueTelegram: (productId: string) => void; onApproveTelegram: (requestId: string) => void; onRetryTelegram: (requestId: string) => void }) {
  const [productUrl, setProductUrl] = useState("");
  const [affiliateUrl, setAffiliateUrl] = useState("");
  const [evidenceUrl, setEvidenceUrl] = useState("");
  const [language, setLanguage] = useState("pt-BR");
  const [sourceKind, setSourceKind] = useState("product_page");
  const [ownerNotes, setOwnerNotes] = useState("");
  const [targetChannel, setTargetChannel] = useState("telegram_public");
  const [trackingLabel, setTrackingLabel] = useState("telegram_public");
  const [channelRegistered, setChannelRegistered] = useState(false);
  const [selectedCandidate, setSelectedCandidate] = useState<ProductResearchCandidate | null>(null);
  const [submissionMessage, setSubmissionMessage] = useState("");
  const [submittedCandidateIds, setSubmittedCandidateIds] = useState<string[]>([]);
  const productFormRef = useRef<HTMLFormElement>(null);
  const productUrlInputRef = useRef<HTMLInputElement>(null);
  const detectedMarketplace = useMemo(() => marketplaceFromUrl(productUrl), [productUrl]);
  const meliLinkRecognized = useMemo(() => isMeliShortUrl(productUrl), [productUrl]);

  useEffect(() => {
    const loadSubmittedCandidates = () => {
      try {
        const stored = JSON.parse(window.localStorage.getItem("factory-submitted-shortlist-candidates") ?? "[]") as unknown;
        setSubmittedCandidateIds(Array.isArray(stored) ? stored.filter((value): value is string => typeof value === "string") : []);
      } catch { setSubmittedCandidateIds([]); }
    };
    const timeoutId = window.setTimeout(loadSubmittedCandidates, 0);
    return () => window.clearTimeout(timeoutId);
  }, []);

  function markCandidateSubmitted(candidateId: string) {
    setSubmittedCandidateIds((current) => {
      const next = [...new Set([...current, candidateId])];
      window.localStorage.setItem("factory-submitted-shortlist-candidates", JSON.stringify(next));
      return next;
    });
  }

  function selectCandidate(candidate: ProductResearchCandidate) {
    setSelectedCandidate(candidate);
    setProductUrl("");
    setAffiliateUrl("");
    setEvidenceUrl(isGenericMarketplaceSource(candidate.source_url) ? "" : candidate.source_url);
    setLanguage("pt-BR");
    setSourceKind("product_page");
    setOwnerNotes(`Selecionado na pesquisa: ${candidate.product_name}. Score ${candidate.score_total}. ${candidate.reasons.join(" ")}`.slice(0, 800));
    setTargetChannel("telegram_public");
    setTrackingLabel("telegram_public");
    setSubmissionMessage("");
    window.setTimeout(() => {
      productFormRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
      productUrlInputRef.current?.focus();
    }, 0);
  }

  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (await onSubmit({ productUrl, affiliateUrl, evidenceUrl, language, sourceKind, ownerNotes, targetChannel, trackingLabel, channelRegistered })) {
      setSubmissionMessage(meliLinkRecognized
        ? "Link Mercado Livre recebido e preservado como link monetizado. Agora ele entrou na análise; nada foi publicado."
        : "Produto recebido para análise. Nada foi publicado.");
      if (selectedCandidate) markCandidateSubmitted(selectedCandidate.candidate_id);
      setProductUrl("");
      setAffiliateUrl("");
      setEvidenceUrl("");
      setLanguage("pt-BR");
      setSourceKind("product_page");
      setOwnerNotes("");
      setTargetChannel("telegram_public");
      setTrackingLabel("telegram_public");
      setChannelRegistered(false);
      setSelectedCandidate(null);
      window.setTimeout(() => window.scrollTo({ top: 0, behavior: "smooth" }), 50);
    }
  }

  return <>
    <ResearchMissionPanel missions={missions} busy={busy} submittedCandidateIds={submittedCandidateIds} onSubmit={onSubmitMission} onSelectCandidate={selectCandidate} onArchiveMission={onArchiveMission} />
    <section className={styles.productWorkspace}>
    <form ref={productFormRef} className={styles.productForm} onSubmit={submit}>
      <SectionHead kicker="NOVA ANÁLISE" title="Adicionar produto" />
      <div className={styles.formBody}>
        {selectedCandidate && <div className={styles.selectedCandidate}>
          <span><Check size={15} /></span>
          <div><small>PRODUTO ESCOLHIDO NA PESQUISA</small><strong>{selectedCandidate.product_name}</strong><p>Agora cole abaixo o link <code>meli.la</code> gerado no Mercado Livre. A fonte da pesquisa já foi anexada como evidência.</p></div>
          <button type="button" onClick={() => setSelectedCandidate(null)} aria-label="Remover seleção"><X size={15} /></button>
        </div>}
        <label><span>Link do produto ou link <code>meli.la</code></span><div><ExternalLink size={16} /><input ref={productUrlInputRef} type="url" required value={productUrl} onChange={(event) => { setProductUrl(event.target.value); setSubmissionMessage(""); }} placeholder="Cole aqui o link meli.la gerado no Mercado Livre" /></div><small>Se você já gerou o link <code>meli.la</code>, cole somente aqui.</small></label>
        {meliLinkRecognized && <div className={styles.recognizedLink}><Check size={15} /><span><strong>Link monetizado reconhecido</strong>Não precisa repetir no campo seguinte.</span></div>}
        <label><span>Link afiliado separado <small>opcional</small></span><div><BadgeDollarSign size={16} /><input type="url" disabled={meliLinkRecognized} value={meliLinkRecognized ? "" : affiliateUrl} onChange={(event) => setAffiliateUrl(event.target.value)} placeholder={meliLinkRecognized ? "Já reconhecido no campo acima" : "Use apenas se for diferente do primeiro link"} /></div><small>Deixe vazio quando o primeiro campo já contém <code>meli.la</code>.</small></label>
        <label><span>Evidência ou página de suporte <small>opcional</small></span><div><FileSearch size={16} /><input type="url" value={evidenceUrl} onChange={(event) => setEvidenceUrl(event.target.value)} placeholder="Página de suporte, print hospedado, termos ou review" /></div></label>
        <div className={styles.formSplit}>
          <label><span>Tipo</span><select value={sourceKind} onChange={(event) => setSourceKind(event.target.value)}><option value="product_page">Produto físico</option><option value="sales_page">Página de venda</option></select></label>
          <label><span>Idioma</span><select value={language} onChange={(event) => setLanguage(event.target.value)}><option value="pt-BR">Português</option><option value="en">Inglês</option><option value="es">Espanhol</option><option value="unknown">Não sei</option></select></label>
        </div>
        <div className={styles.formSplit}>
          <label><span>Canal da oferta</span><select value={targetChannel} onChange={(event) => { const next = event.target.value; setTargetChannel(next); setTrackingLabel(next); }}><option value="telegram_public">Telegram público</option></select><small>WhatsApp fica fora desta fase.</small></label>
          <label><span>Etiqueta no Mercado Livre</span><input value={trackingLabel} maxLength={48} onChange={(event) => setTrackingLabel(event.target.value)} placeholder="telegram_public" /><small>Use esta etiqueta ao gerar o link no painel oficial.</small></label>
        </div>
        {detectedMarketplace === "Mercado Livre" && <label className={styles.channelConfirmation}><input type="checkbox" checked={channelRegistered} onChange={(event) => setChannelRegistered(event.target.checked)} /><span>Este canal público já está cadastrado no meu perfil de afiliado do Mercado Livre.</span></label>}
        <label><span>Contexto para os funcionários <small>opcional</small></span><textarea value={ownerNotes} onChange={(event) => setOwnerNotes(event.target.value)} maxLength={800} placeholder="Ex: vi essa oferta na Digistore, comissão boa, mas ainda falta PayPal. Quero avaliar promessa, público e risco." /></label>
        <div className={styles.acceptedMarkets} aria-label="Plataformas reconhecidas">{["Amazon Brasil", "Mercado Livre", "Shopee", "Adidas", "Digistore24", "Braip"].map((marketplace) => <span key={marketplace} className={detectedMarketplace === marketplace ? styles.marketActive : ""}>{marketplace}</span>)}</div>
        <button className={styles.submitProduct} disabled={busy === "product"}><PackagePlus size={17} /> {busy === "product" ? "Enviando..." : "Enviar para análise"}</button>
        {submissionMessage && <div className={styles.submissionConfirmation} role="status"><Check size={16} /><span><strong>Envio concluído</strong>{submissionMessage}</span></div>}
        <p className={styles.formSafety}><ShieldCheck size={15} /> Gere o link no painel oficial com a etiqueta acima. A fábrica preserva, analisa e prepara a copy; nenhum anúncio, compra ou publicação começa aqui.</p>
      </div>
    </form>
    <div className={styles.productQueue}>
      <SectionHead kicker="ACOMPANHAMENTO" title="Produtos e pacotes" />
      {items.some((item) => item.campaignPackage) && <CampaignComparison items={items.filter((item) => item.campaignPackage)} busy={busy} onPrepareBrief={onPrepareBrief} />}
      {items.length ? <div className={styles.productList}>{items.map((item) => <ProductIntakeRow key={item.id} item={item} publication={publications.find((entry) => entry.productId === item.id)} busy={busy} onPrepareCampaign={onPrepareCampaign} onPrepareBrief={onPrepareBrief} onRetryAnalysis={onRetryAnalysis} onCompleteCommercial={onCompleteCommercial} onQueueTelegram={onQueueTelegram} onApproveTelegram={onApproveTelegram} onRetryTelegram={onRetryTelegram} />)}</div> : <div className={styles.empty}>Nenhum produto enviado ainda.</div>}
    </div>
    </section>
  </>;
}

function ResearchMissionPanel({ missions, busy, submittedCandidateIds, onSubmit, onSelectCandidate, onArchiveMission }: { missions: ProductResearchMissionItem[]; busy: string | null; submittedCandidateIds: string[]; onSubmit: (input: ResearchMissionFormInput) => Promise<boolean>; onSelectCandidate: (candidate: ProductResearchCandidate) => void; onArchiveMission: (missionId: string) => void }) {
  const [goal, setGoal] = useState("");
  const [marketplace, setMarketplace] = useState("mercado_livre");
  const [category, setCategory] = useState("");
  const [maxPrice, setMaxPrice] = useState("");
  const [timeframe, setTimeframe] = useState("week");
  const [resultLimit, setResultLimit] = useState(5);
  const [targetChannel, setTargetChannel] = useState("telegram_public");

  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const accepted = await onSubmit({ goal, marketplaces: [marketplace], category, maxPrice, timeframe, resultLimit, targetChannel });
    if (accepted) { setGoal(""); setCategory(""); setMaxPrice(""); }
  }

  return <section className={styles.researchMissionPanel}>
    <form className={styles.researchMissionComposer} onSubmit={submit}>
      <SectionHead kicker="MISSÃO DE PESQUISA" title="Pedir pesquisa aos funcionários" />
      <div className={styles.formBody}>
        <label><span>O que você quer encontrar?</span><textarea required minLength={2} maxLength={120} value={goal} onChange={(event) => setGoal(event.target.value)} placeholder="Ex: ofertas de tecnologia até R$ 300 com boa procura e imagem limpa" /></label>
        <div className={styles.missionControls}>
          <label><span>Marketplace</span><select value={marketplace} onChange={(event) => setMarketplace(event.target.value)}><option value="mercado_livre">Mercado Livre conectado</option><option value="amazon">Amazon pendente</option><option value="shopee">Shopee pendente</option></select></label>
          <label><span>Período</span><select value={timeframe} onChange={(event) => setTimeframe(event.target.value)}><option value="today">Hoje</option><option value="week">Esta semana</option><option value="evergreen">Oportunidade contínua</option></select></label>
          <label><span>Preço máximo</span><input type="number" min="1" step="1" value={maxPrice} onChange={(event) => setMaxPrice(event.target.value)} placeholder="Sem limite" /></label>
          <label><span>Resultados</span><select value={resultLimit} onChange={(event) => setResultLimit(Number(event.target.value))}>{[3, 5, 8, 10].map((value) => <option key={value} value={value}>{value}</option>)}</select></label>
          <label><span>Categoria <small>opcional</small></span><input value={category} maxLength={80} onChange={(event) => setCategory(event.target.value)} placeholder="Ex: games, casa" /></label>
          <label><span>Canal pensado</span><select value={targetChannel} onChange={(event) => setTargetChannel(event.target.value)}><option value="telegram_public">Telegram público</option><option value="youtube">YouTube</option><option value="instagram">Instagram</option></select></label>
        </div>
        <button className={styles.submitProduct} disabled={busy === "research-mission"}><Sparkles size={17} />{busy === "research-mission" ? "Registrando..." : "Iniciar pesquisa"}</button>
        <p className={styles.formSafety}><ShieldCheck size={15} /> Pesquisa somente leitura. O resultado pede sua confirmação do link monetizado antes de qualquer produção.</p>
      </div>
    </form>
    <div className={styles.researchMissionResults}>
      <SectionHead kicker="RETORNO VISUAL" title="Pesquisas e shortlist" />
      {missions.length ? missions.map((mission) => <ResearchMissionCard key={mission.id} mission={mission} busy={busy} submittedCandidateIds={submittedCandidateIds} onSelectCandidate={onSelectCandidate} onArchiveMission={onArchiveMission} />) : <div className={styles.empty}>Crie uma missão simples. Os funcionários devolverão produtos, evidências, score e pendências aqui.</div>}
    </div>
  </section>;
}

function ResearchMissionCard({ mission, busy, submittedCandidateIds, onSelectCandidate, onArchiveMission }: { mission: ProductResearchMissionItem; busy: string | null; submittedCandidateIds: string[]; onSelectCandidate: (candidate: ProductResearchCandidate) => void; onArchiveMission: (missionId: string) => void }) {
  const shortlist = mission.result.shortlisted ?? [];
  const status = mission.status === "queued" ? "Na fila" : mission.status === "researching" ? "Pesquisando" : mission.status === "review" ? "Sua revisão" : mission.status === "needs_input" ? "Precisa de dados" : "Bloqueada";
  return <article className={styles.researchMissionCard}>
    <div className={styles.missionHeader}><span><small>{status}</small><strong>{mission.goal}</strong></span><span className={styles.missionHeaderActions}><b>{mission.marketplaces.join(" + ")}</b><button type="button" disabled={busy === `archive-research-${mission.id}`} onClick={() => onArchiveMission(mission.id)} title="Arquivar esta pesquisa de teste" aria-label={`Arquivar pesquisa ${mission.goal}`}><X size={13} /></button></span></div>
    <p>{mission.error || (shortlist.length ? `${shortlist.length} produto(s) selecionado(s) para você comparar.` : "Aguardando o funcionário consultar fontes conectadas.")}</p>
    {shortlist.length > 0 && <div className={styles.missionShortlist}>{[...shortlist].sort((a, b) => Number(submittedCandidateIds.includes(a.candidate_id)) - Number(submittedCandidateIds.includes(b.candidate_id))).map((candidate) => {
      const submitted = submittedCandidateIds.includes(candidate.candidate_id);
      const genericSource = isGenericMarketplaceSource(candidate.source_url);
      const sourceUrl = genericSource ? mercadoLivreSearchUrl(candidate.product_name) : candidate.source_url;
      return <div className={`${styles.shortlistCandidate} ${submitted ? styles.shortlistCandidateDone : ""}`} key={candidate.candidate_id}>
      {candidate.image_url ? <Image unoptimized src={candidate.image_url} alt="" width={48} height={48} /> : <span className={styles.shortlistImage}><ShoppingBag size={17} /></span>}
      <span><strong>{candidate.product_name}</strong><small>R$ {candidate.current_price.toFixed(2).replace(".", ",")} · score {candidate.score_total}</small><em>{submitted ? "Enviado para análise · nada publicado" : genericSource ? "Fonte genérica · escolha um anúncio exato" : "Link monetizado: aguardando você"}</em></span>
      <div className={styles.shortlistActions}><button type="button" disabled={submitted} onClick={() => onSelectCandidate(candidate)}>{submitted ? <><Check size={13} /> Enviado</> : <><Check size={13} /> Escolher produto</>}</button><a href={sourceUrl} target="_blank" rel="noreferrer">{genericSource ? "Buscar produto" : "Abrir fonte"} <ExternalLink size={12} /></a></div>
    </div>; })}</div>}
    <footer><span>Provider: não chamado</span><span>Publicação: bloqueada</span></footer>
  </article>;
}

function ProductIntakeRow({ item, publication, busy, onPrepareCampaign, onPrepareBrief, onRetryAnalysis, onCompleteCommercial, onQueueTelegram, onApproveTelegram, onRetryTelegram }: { item: ProductIntakeItem; publication?: TelegramPublication; busy: string | null; onPrepareCampaign: (productId: string) => void; onPrepareBrief: (productId: string) => void; onRetryAnalysis: (productId: string) => void; onCompleteCommercial: (productId: string, input: CommercialFormInput) => Promise<boolean>; onQueueTelegram: (productId: string) => void; onApproveTelegram: (requestId: string) => void; onRetryTelegram: (requestId: string) => void }) {
  const stage = item.status === "queued" ? 1 : item.status === "analyzing" ? 2 : item.status === "needs_input" ? 4 : item.status === "completed" ? 5 : 2;
  const status = item.status === "queued" ? "Recebido" : item.status === "analyzing" ? "Analisando" : item.status === "needs_input" ? "Precisa de você" : item.status === "completed" ? "Pronto para decisão" : "Bloqueado";
  const [currentPrice, setCurrentPrice] = useState(item.currentPrice ? String(item.currentPrice).replace(".", ",") : "");
  const [oldPrice, setOldPrice] = useState(item.oldPrice ? String(item.oldPrice).replace(".", ",") : "");
  const [commissionConfirmed, setCommissionConfirmed] = useState(item.commissionConfirmed);
  const [channelRegistered, setChannelRegistered] = useState(item.channelRegistered);
  const [creativeReviewStatus, setCreativeReviewStatus] = useState<CommercialFormInput["creativeReviewStatus"]>(item.creativeReviewStatus === "custom_creative_approved" ? "custom_creative_approved" : "official_link_preview");
  const [finalApproval, setFinalApproval] = useState(false);
  const publishBlockers = item.campaignPackage?.missingToPublish.filter((field) => field !== "aprovação final do owner") ?? [];

  async function submitCommercial(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await onCompleteCommercial(item.id, { currentPrice, oldPrice, commissionConfirmed, channelRegistered, creativeReviewStatus });
  }

  return <article className={styles.productRow}>
    <div className={styles.productIdentity}>
      {item.imageUrl ? <Image unoptimized src={item.imageUrl} alt="Imagem coletada do produto" width={54} height={54} /> : <span><ShoppingBag size={20} /></span>}
      <div><small>{item.marketplace}</small><strong>{item.productName || "Produto aguardando coleta"}</strong><a href={item.productUrl} target="_blank" rel="noreferrer">Abrir produto <ExternalLink size={12} /></a></div>
      <b className={item.status === "blocked" ? styles.red : item.status === "completed" ? styles.green : styles.amber}>{status}</b>
    </div>
    <div className={styles.productStages} aria-label={`Etapa ${stage} de 5`}>
      {["Recebido", "Dados", "Imagem", "Afiliado", "Decisão"].map((label, index) => <span key={label} className={index < stage ? styles.stageDone : ""}><i>{index < stage ? <Check size={11} /> : index + 1}</i>{label}</span>)}
    </div>
    <p>{item.analysisSummary}</p>
    {(item.promiseReview || item.creativeRecommendation || item.funnelSuggestion || item.affiliateReadiness) && <div className={styles.productInsights}>
      {item.promiseReview && <span><strong>Promessa</strong>{item.promiseReview}</span>}
      {item.creativeRecommendation && <span><strong>Criativo</strong>{item.creativeRecommendation}</span>}
      {item.commissionNotes && <span><strong>Comissão</strong>{item.commissionNotes}</span>}
      {item.funnelSuggestion && <span><strong>Funil</strong>{item.funnelSuggestion}</span>}
      {item.affiliateReadiness && <span><strong>Próximo fluxo</strong>{item.affiliateReadiness}</span>}
    </div>}
    <div className={styles.productMeta}>
      <span>{item.sourceKind === "sales_page" ? "Página de venda" : "Produto físico"}</span>
      <span>{item.language === "en" ? "Inglês" : item.language === "es" ? "Espanhol" : item.language === "pt-BR" ? "Português" : "Idioma indefinido"}</span>
      <span>Telegram público · etiqueta {item.trackingLabel}</span>
      {item.evidenceUrl && <a href={item.evidenceUrl} target="_blank" rel="noreferrer">Abrir evidência <ExternalLink size={12} /></a>}
    </div>
    {item.ownerNotes && <blockquote className={styles.ownerNotes}>{item.ownerNotes}</blockquote>}
    {item.missingFields.length > 0 && <div className={styles.missingFields}>{item.missingFields.map((field) => <span key={field}>{field.replaceAll("_", " ")}</span>)}</div>}
    {!item.affiliateProvided && <div className={styles.affiliatePending}><CircleAlert size={14} /> Link afiliado ainda não informado</div>}
    {item.marketplace === "Mercado Livre" && !item.channelRegistered && <div className={styles.affiliatePending}><CircleAlert size={14} /> Confirme o cadastro deste canal público no programa do Mercado Livre antes de publicar.</div>}
    {(item.status === "needs_input" || item.status === "blocked") && <button className={styles.prepareCampaign} disabled={busy === `retry-${item.id}`} onClick={() => onRetryAnalysis(item.id)}><RefreshCw size={15} /> {busy === `retry-${item.id}` ? "Reenviando..." : "Reanalisar página"}</button>}
    {(item.status === "completed" || item.status === "needs_input") && !item.campaignPackage && <button className={styles.prepareCampaign} disabled={busy === `campaign-${item.id}`} onClick={() => onPrepareCampaign(item.id)}><Sparkles size={15} /> {busy === `campaign-${item.id}` ? "Preparando..." : "Preparar pacote sem gasto"}</button>}
    {(item.status === "completed" || item.status === "needs_input") && item.affiliateProvided && <form className={styles.commercialConfirmation} onSubmit={submitCommercial}>
      <div className={styles.commercialHeading}><span><BadgeDollarSign size={16} /><strong>Confirmação comercial</strong></span><small>Dados conferidos por você na página oficial</small></div>
      <div className={styles.commercialGrid}>
        <label><span>Preço atual</span><input required inputMode="decimal" value={currentPrice} onChange={(event) => setCurrentPrice(event.target.value)} placeholder="Ex: 69,90" /></label>
        <label><span>Preço anterior <small>opcional</small></span><input inputMode="decimal" value={oldPrice} onChange={(event) => setOldPrice(event.target.value)} placeholder="Ex: 99,90" /></label>
        <label><span>Imagem para a postagem</span><select value={creativeReviewStatus} onChange={(event) => setCreativeReviewStatus(event.target.value as CommercialFormInput["creativeReviewStatus"])}><option value="official_link_preview">Usar prévia oficial do link</option><option value="custom_creative_approved">Criativo próprio já revisado</option></select></label>
      </div>
      <label className={styles.confirmationCheck}><input type="checkbox" checked={commissionConfirmed} onChange={(event) => setCommissionConfirmed(event.target.checked)} /><span>Este link foi gerado no meu programa oficial de afiliados.</span></label>
      <label className={styles.confirmationCheck}><input type="checkbox" checked={channelRegistered} onChange={(event) => setChannelRegistered(event.target.checked)} /><span>O canal Telegram está cadastrado como canal público no Mercado Livre.</span></label>
      <button className={styles.prepareCampaign} disabled={busy === `commercial-${item.id}`}><Check size={15} /> {busy === `commercial-${item.id}` ? "Salvando..." : "Salvar e atualizar a prévia"}</button>
    </form>}
    {item.campaignPackage && <div className={styles.campaignPackageDetail}>
      <strong>Pacote de campanha</strong>
      <span><b>Canal</b>{item.campaignPackage.channel}</span>
      <span><b>Custo</b>{item.campaignPackage.estimatedCost}</span>
      <span><b>Risco</b>{item.campaignPackage.risk}</span>
      <div className={styles.telegramPreview}><b>Prévia exata no Telegram</b><pre>{item.campaignPackage.copy}</pre></div>
      <small><ShieldCheck size={13} /> Publicação bloqueada até resolver {item.campaignPackage.missingToPublish.length} pendência(s).</small>
      {!item.campaignPackage.organicBrief && <button className={styles.prepareCampaign} disabled={busy === `brief-${item.id}`} onClick={() => onPrepareBrief(item.id)}><Sparkles size={15} /> {busy === `brief-${item.id}` ? "Criando briefing..." : "Transformar em briefing orgânico"}</button>}
      {item.campaignPackage.organicBrief && <OrganicBriefCard brief={item.campaignPackage.organicBrief} />}
      {!publication && <div className={styles.telegramApproval}>
        <div><Send size={17} /><span><strong>Preparar candidato para @achadosbaratosBrasil</strong><small>Esta etapa apenas registra a prévia. Uma aprovação separada será exigida.</small></span></div>
        {publishBlockers.length > 0 && <p><CircleAlert size={14} /> Resolva antes: {publishBlockers.join(", ")}.</p>}
        <label className={styles.confirmationCheck}><input type="checkbox" checked={finalApproval} onChange={(event) => setFinalApproval(event.target.checked)} /><span>Revisei esta prévia e quero criar um candidato pendente. Isto não autoriza envio.</span></label>
        <button className={styles.telegramPublishButton} disabled={!finalApproval || publishBlockers.length > 0 || busy === `telegram-${item.id}`} onClick={() => onQueueTelegram(item.id)}><Send size={15} /> {busy === `telegram-${item.id}` ? "Preparando..." : "Preparar candidato para aprovação"}</button>
      </div>}
      {publication && <TelegramPublicationStatus publication={publication} busy={busy} onApprove={onApproveTelegram} onRetry={onRetryTelegram} />}
    </div>}
  </article>;
}

function TelegramPublicationStatus({ publication, busy, onApprove, onRetry }: { publication: TelegramPublication; busy: string | null; onApprove: (requestId: string) => void; onRetry: (requestId: string) => void }) {
  const [approvalChecked, setApprovalChecked] = useState(false);
  const label = publication.status === "pending_approval" ? "PENDING HUMAN APPROVAL" : publication.status === "queued" ? "Na fila segura" : publication.status === "publishing" ? "Enviando" : publication.status === "sent" ? "Publicado" : publication.status === "failed" ? "Falhou" : "Cancelado";
  return <div className={`${styles.telegramStatus} ${publication.status === "sent" ? styles.telegramSent : publication.status === "failed" ? styles.telegramFailed : ""}`}>
    <div><Radio size={17} /><span><strong>{label}</strong><small>{publication.chatId}</small></span></div>
    <div className={styles.telegramPreview}><b>Conteúdo exato do candidato</b><pre>{publication.messageText}</pre></div>
    <div className={styles.candidateFacts}>
      <span><b>Título interno</b>{publication.candidate.internalTitle}</span><span><b>Objetivo</b>{publication.candidate.objective}</span>
      <span><b>Público</b>{publication.candidate.audience}</span><span><b>CTA neutro</b>{publication.candidate.callToAction}</span>
      <span><b>Origem</b>{publication.candidate.origin}</span><span><b>Validade</b>{publication.candidate.validUntil ? new Date(publication.candidate.validUntil).toLocaleString("pt-BR") : "Não informada"}</span>
      <span><b>Riscos</b>{publication.candidate.risks?.join(" · ") || "Não registrados"}</span><span><b>Idempotência</b>{publication.candidate.idempotencyKey}</span>
    </div>
    <p><ShieldCheck size={14} /> STATUS: {publication.candidate.publicationMode || "REAL CONTROLADO - OPT-IN E APROVACAO"} · PUBLICAÇÃO: {publication.status === "sent" ? "EXECUTADA" : "NÃO EXECUTADA"}</p>
    {publication.status === "pending_approval" && <div className={styles.telegramApproval}>
      <label className={styles.confirmationCheck}><input type="checkbox" checked={approvalChecked} onChange={(event) => setApprovalChecked(event.target.checked)} /><span>Conferi conteúdo, destino, validade e riscos. Quero colocar este candidato na fila local.</span></label>
      <button className={styles.telegramPublishButton} disabled={!approvalChecked || busy === `telegram-approve-${publication.id}`} onClick={() => onApprove(publication.id)}><Check size={15} /> {busy === `telegram-approve-${publication.id}` ? "Aprovando..." : "Aprovar e colocar na fila"}</button>
      <small>Esta aprovação não executa o worker e não envia mensagem ao Telegram.</small>
    </div>}
    {publication.status === "sent" && <p><Check size={14} /> Mensagem #{publication.telegramMessageId} enviada em {publication.sentAt ? new Date(publication.sentAt).toLocaleString("pt-BR") : "horário registrado"}.</p>}
    {publication.status === "queued" && <p><Clock3 size={14} /> Aguardando o worker local autorizado. Nenhum segundo envio será criado.</p>}
    {publication.status === "publishing" && <p><RefreshCw size={14} /> O worker reservou esta mensagem e está aguardando a confirmação do Telegram.</p>}
    {publication.status === "failed" && <><p><CircleAlert size={14} /> {publication.error || "O Telegram não confirmou o envio."}</p><button className={styles.prepareCampaign} disabled={busy === `telegram-retry-${publication.id}`} onClick={() => onRetry(publication.id)}><RefreshCw size={14} /> {busy === `telegram-retry-${publication.id}` ? "Reenfileirando..." : "Tentar novamente"}</button></>}
  </div>;
}

function CampaignComparison({ items, busy, onPrepareBrief }: { items: ProductIntakeItem[]; busy: string | null; onPrepareBrief: (productId: string) => void }) {
  return <section className={styles.campaignComparison}>
    <div><small>COMPARAÇÃO SEM GASTO</small><strong>Pacotes preparados</strong><span>Escolha o melhor caminho depois de comparar evidência, canal, risco e pendências.</span></div>
    <div className={styles.campaignTable}>
      {items.map((item) => item.campaignPackage && <article key={item.id}>
        <strong>{item.campaignPackage.product}</strong>
        <span><b>Canal</b>{item.campaignPackage.channel}</span>
        <span><b>Criativo</b>{item.campaignPackage.creative}</span>
        <span><b>Risco</b>{item.campaignPackage.risk}</span>
        <span><b>Custo estimado</b>{item.campaignPackage.estimatedCost}</span>
        <em>{item.campaignPackage.missingToPublish.length} pendência(s) antes de publicar</em>
        {!item.campaignPackage.organicBrief ? <button className={styles.selectCampaign} disabled={busy === `brief-${item.id}`} onClick={() => onPrepareBrief(item.id)}><Sparkles size={14} /> {busy === `brief-${item.id}` ? "Criando..." : "Criar briefing orgânico"}</button> : <small className={styles.briefReady}><Check size={13} /> Briefing preparado</small>}
      </article>)}
    </div>
  </section>;
}

function OrganicBriefCard({ brief }: { brief: NonNullable<NonNullable<ProductIntakeItem["campaignPackage"]>["organicBrief"]> }) {
  return <section className={styles.organicBrief}>
    <div><b>Briefing orgânico</b><strong>{brief.status === "blocked" ? "Com pendências" : "Pronto para sua revisão"}</strong></div>
    <span><b>Objetivo</b>{brief.goal}</span>
    <span><b>Público</b>{brief.audience}</span>
    <span><b>Ângulo</b>{brief.angle}</span>
    <span><b>Formato</b>{brief.format}</span>
    <span><b>Métricas</b>{brief.metricsToCollect.join(" · ")}</span>
    <small><ShieldCheck size={13} /> Provider não chamado · publicação bloqueada</small>
  </section>;
}

function OpportunitiesView({ visible, selected, filter, category, query, busy, onFilter, onCategory, onQuery, onSelect, onSynchronize, onDecide }: {
  visible: Opportunity[];
  selected?: Opportunity;
  filter: OpportunityStatus | "all";
  category: CategoryFilter;
  query: string;
  busy: string | null;
  onFilter: (value: OpportunityStatus | "all") => void;
  onCategory: (value: CategoryFilter) => void;
  onQuery: (value: string) => void;
  onSelect: (id: string) => void;
  onSynchronize: () => void;
  onDecide: (action: "approve" | "reject") => void;
}) {
  return <section className={styles.workspace}>
    <div className={styles.queue}>
      <SectionHead kicker="FILA PRIORITÁRIA" title="Insights e decisões" action={<button className={styles.iconText} disabled={busy === "sync"} onClick={onSynchronize}><RefreshCw size={16} /> {busy === "sync" ? "Sincronizando" : "Sincronizar fila"}</button>} />
      <div className={styles.filters}>
        <label className={styles.searchBox}><Search size={16} /><input value={query} onChange={(event) => onQuery(event.target.value)} placeholder="Buscar por título, canal ou funcionário" /></label>
        <div className={styles.filterTabs} aria-label="Filtrar por estado">
          {(["all", "pending", "approved", "production", "review", "blocked"] as const).map((item) => <button key={item} className={filter === item ? styles.filterActive : ""} onClick={() => onFilter(item)}>{item === "all" ? "Todas" : statusLabel[item]}</button>)}
        </div>
      </div>
      <div className={styles.categoryTabs} aria-label="Filtrar por tipo">
        {(["all", "Notícia", "Oferta", "Vídeo curto", "Integração"] as const).map((item) => <button key={item} className={category === item ? styles.categoryActive : ""} onClick={() => onCategory(item)}>{item === "all" ? "Todos os tipos" : item}</button>)}
      </div>
      <div className={styles.tableWrap}>
        <table>
          <thead><tr><th>Oportunidade</th><th>Canal</th><th>Score</th><th>Status</th><th><span className="sr-only">Abrir</span></th></tr></thead>
          <tbody>{visible.map((item) => <tr key={item.id} className={selected?.id === item.id ? styles.selectedRow : ""} onClick={() => onSelect(item.id)}><td><strong>{item.title}</strong><small>{item.source} · {item.updatedAt}</small></td><td>{item.channel}</td><td><b className={styles.score}>{item.score}</b></td><td><Status status={item.status} /></td><td><button aria-label={`Abrir ${item.title}`} onClick={() => onSelect(item.id)}><ChevronRight size={17} /></button></td></tr>)}</tbody>
        </table>
        {!visible.length && <div className={styles.empty}>Nenhuma oportunidade corresponde aos filtros.</div>}
      </div>
    </div>
    {selected && <OpportunityDetail selected={selected} busy={busy} onDecide={onDecide} />}
  </section>;
}

function OpportunityDetail({ selected, busy, onDecide }: { selected: Opportunity; busy: string | null; onDecide: (action: "approve" | "reject") => void }) {
  return <aside className={styles.detail} aria-label="Detalhes da oportunidade selecionada">
    <div className={styles.detailTop}><Status status={selected.status} /><span className={styles.confidence}>{selected.confidence}% confiança</span></div>
    <p className={styles.kicker}>{selected.category} / {selected.channel}</p>
    <h2>{selected.title}</h2>
    <p className={styles.detailSummary}>{selected.summary}</p>
    <div className={styles.signalGrid}><div><span>Score</span><strong>{selected.score}/100</strong></div><div><span>Prioridade</span><strong>{selected.priority === "high" ? "Alta" : selected.priority === "medium" ? "Média" : "Baixa"}</strong></div></div>
    <div className={styles.assessment}><span><ShieldCheck size={15} /> Risco</span><p>{selected.risk}</p><span><Sparkles size={15} /> Próxima ação</span><p>{selected.nextAction}</p></div>
    <div className={styles.sources}>
      <span><ExternalLink size={14} /> Fontes para conferência</span>
      {selected.sources.length ? selected.sources.map((source) => <a key={source.id} href={source.url} target="_blank" rel="noreferrer"><span><strong>{source.label}</strong><small>{source.sourceType === "official" ? "Fonte oficial" : source.sourceType === "marketplace" ? "Marketplace" : "Referência"}</small></span><ExternalLink size={14} /></a>) : <p>Nenhuma fonte clicável registrada.</p>}
    </div>
    {selected.status === "pending" ? <>
      <div className={styles.decisionActions}><button className={styles.approve} disabled={Boolean(busy)} onClick={() => onDecide("approve")}><Check size={17} /> {busy === "approve" ? "Criando fila..." : "Aprovar rascunho"}</button><button className={styles.reject} disabled={Boolean(busy)} onClick={() => onDecide("reject")}><X size={17} /> Rejeitar</button></div>
      <div className={styles.safety}><ShieldCheck size={16} /><span>Cria apenas uma solicitação MOCK. Áudio, vídeo final, publicação e gastos exigem outras aprovações.</span></div>
    </> : <div className={styles.safety}><ShieldCheck size={16} /><span>{selected.status === "review" ? "O rascunho está na área Produção para sua revisão." : selected.status === "approved" ? "Solicitação na fila MOCK; publicação continua bloqueada." : selected.status === "production" ? "Funcionários trabalhando; publicação continua bloqueada." : "Esta oportunidade não pode avançar enquanto estiver bloqueada."}</span></div>}
  </aside>;
}

function ProductionView({ productions, busy, onDiscard, onApproveMedia, onSelectProviderPlan }: { productions: ProductionRequest[]; busy: string | null; onDiscard: (id: string) => void; onApproveMedia: (id: string) => void; onSelectProviderPlan: (id: string, planId: "local_free" | "hybrid_quality") => void }) {
  const [selectedId, setSelectedId] = useState(productions[0]?.id ?? "");
  const selectedRun = productions.find((run) => run.id === selectedId) ?? productions[0];
  return <section className={styles.pageSection}>
    <SectionHead kicker="STATUS POR TRABALHO" title="Fila de produção e revisão" />
    <div className={styles.pipelineList}>
      {productions.length ? productions.map((run) => <PipelineRow
        key={run.id}
        icon={run.category.toLowerCase().includes("oferta") || run.category.toLowerCase().includes("produto") ? <BadgeDollarSign /> : <Newspaper />}
        title={run.title}
        department={productionStage(run.status).department}
        progress={productionStage(run.status).progress}
        tone={run.status === "review" || run.status === "media_review" ? "green" : run.status === "failed" ? "amber" : "cyan"}
        note={productionStage(run.status).note || run.reviewNotes}
        selected={run.id === selectedRun?.id}
        onClick={() => setSelectedId(run.id)}
      />) : <div className={styles.empty}>Nenhuma solicitação de produção foi aprovada ainda.</div>}
    </div>
    {selectedRun?.status === "review"
      ? <ProductionDraft run={selectedRun} busy={Boolean(busy)} onDiscard={onDiscard} onApproveMedia={onApproveMedia} />
      : selectedRun?.status === "media_review" && selectedRun.media
        ? <ProductionMediaReview run={selectedRun} busy={Boolean(busy)} onSelectProviderPlan={onSelectProviderPlan} />
      : selectedRun ? <ProductionStatusDetail run={selectedRun} /> : null}
    <div className={styles.explainerBand}><ShieldCheck size={20} /><div><strong>Como funciona esta área</strong><p>A porcentagem indica etapas concluídas, não tempo. Primeiro você aprova o roteiro; depois pode autorizar a pré-produção MOCK. Provider real, arquivo final, custo e publicação continuam em gates separados.</p></div></div>
  </section>;
}

function ProductionStatusDetail({ run }: { run: ProductionRequest }) {
  const brandImage = run.channel.toLowerCase().includes("game") ? "/brands/fase-nova-games.png" : "/brands/achados-baratos.png";
  return <article className={styles.productionDraft}>
    <div className={styles.productionIdentity}>
      <img src={brandImage} alt={`Identidade do canal ${run.channel}`} />
      <div><span>{run.status === "queued" ? "AGUARDANDO ANÁLISE" : "PRODUÇÃO BLOQUEADA"}</span><h2>{run.title}</h2><p>{run.channel} · {run.category}</p></div>
      <Status status={run.status === "queued" ? "approved" : "blocked"} />
    </div>
    <div className={styles.statusExplanation}><strong>{run.status === "queued" ? "O que acontecerá agora" : "Por que não avançou"}</strong><p>{run.reviewNotes}</p></div>
    <div className={styles.sources}><span><ExternalLink size={14} /> Fontes disponíveis</span>{run.sources.length ? run.sources.map((source) => <a key={source.id} href={source.url} target="_blank" rel="noreferrer"><span><strong>{source.label}</strong><small>{source.sourceType}</small></span><ExternalLink size={14} /></a>) : <p>Nenhuma fonte específica foi coletada.</p>}</div>
    <div className={styles.safety}><ImageIcon size={16} /><span>Esta é a identidade do canal. Uma imagem real do produto ou notícia só aparecerá depois da coleta e da revisão de direitos/qualidade.</span></div>
  </article>;
}

function ProductionDraft({ run, busy, onDiscard, onApproveMedia }: { run: ProductionRequest; busy: boolean; onDiscard: (id: string) => void; onApproveMedia: (id: string) => void }) {
  return <article className={styles.productionDraft}>
    <div className={styles.draftHeader}><div><span>RASCUNHO PARA REVISÃO</span><h2>{run.title}</h2></div><Status status="review" /></div>
    <div className={styles.draftGrid}>
      <div><span>Gancho</span><p>{run.hook}</p></div>
      <div><span>Chamada final</span><p>{run.callToAction}</p></div>
    </div>
    <div className={styles.draftScript}><span>Roteiro</span><p>{run.script}</p></div>
    <div className={styles.assetPlan}><span>Plano visual</span>{run.assetPlan.map((asset) => <p key={asset}><Check size={13} /> {asset}</p>)}</div>
    <div className={styles.safety}><ShieldCheck size={16} /><span>{run.reviewNotes} Publicação: bloqueada.</span></div>
    <div className={styles.decisionActions}><button className={styles.approve} disabled={busy} onClick={() => onApproveMedia(run.opportunityId)}><Check size={17} /> {busy ? "Processando..." : "Aprovar pré-produção MOCK"}</button><button className={styles.reject} disabled={busy} onClick={() => onDiscard(run.opportunityId)}><X size={17} /> Descartar rascunho</button></div>
  </article>;
}

function ProductionMediaReview({ run, busy, onSelectProviderPlan }: { run: ProductionRequest; busy: boolean; onSelectProviderPlan: (id: string, planId: "local_free" | "hybrid_quality") => void }) {
  const media = run.media!;
  return <article className={styles.productionDraft}>
    <div className={styles.draftHeader}><div><span>PRÉ-PRODUÇÃO PARA REVISÃO</span><h2>{run.title}</h2></div><Status status="review" /></div>
    <div className={styles.mediaReviewGrid}>
      {(["audio", "image", "video"] as const).map((key) => <div key={key}><span>{media.departments[key]?.label ?? key}</span><strong>{media.departments[key]?.status === "planned" ? "Plano validado" : "Pendente"}</strong><p>{media.departments[key]?.summary ?? "O departamento não devolveu um plano."}</p></div>)}
    </div>
    <div className={styles.statusExplanation}><strong>O que foi produzido</strong><p>{media.reviewNotes}</p></div>
    <div className={styles.providerQuoteHeader}><div><span>TERCEIRO PORTÃO</span><h3>Escolha o orçamento, não a execução</h3></div><strong>US$ 0 gastos</strong></div>
    <div className={styles.providerQuoteGrid}>
      {media.providerPlans.map((plan) => <section key={plan.planId} className={media.selectedProviderPlan === plan.planId ? styles.providerQuoteSelected : ""}>
        <div className={styles.providerQuoteTop}><div><span>{plan.completePrice ? "ORÇAMENTO COMPLETO" : "ESTIMATIVA PARCIAL"}</span><h4>{plan.displayName}</h4></div><strong>{plan.estimatedCostUsd === 0 ? "US$ 0,00" : `a partir de US$ ${plan.estimatedCostUsd.toFixed(2).replace(".", ",")}`}</strong></div>
        <p>Duração estimada: {plan.estimatedDurationSeconds}s</p>
        <div className={styles.providerQuoteItems}>{plan.items.map((item) => <div key={item.department}><span>{item.department}</span><strong>{item.displayName}</strong><small>{item.limitation}</small></div>)}</div>
        <p className={styles.providerQuoteWarning}>{plan.warning}</p>
        <button disabled={busy || media.selectedProviderPlan === plan.planId} onClick={() => onSelectProviderPlan(run.opportunityId, plan.planId)}>{media.selectedProviderPlan === plan.planId ? "Plano selecionado" : plan.planId === "local_free" ? "Selecionar plano gratuito" : "Guardar para usar depois"}</button>
      </section>)}
    </div>
    <div className={styles.safety}><ShieldCheck size={16} /><span>Provider: {media.providerStatus === "planned_not_called" ? "planejado, não chamado" : "não chamado"} · arquivo final: não gerado · publicação: bloqueada · execução: bloqueada · qualidade do plano: {media.qualityPassed ? "aprovada" : "requer correção"}.</span></div>
  </article>;
}

function productionStage(status: ProductionRequest["status"]) {
  if (status === "queued") return { progress: 10, department: "Fila → Script Department", note: "Aguardando funcionário MOCK" };
  if (status === "production") return { progress: 25, department: "Script Department", note: "Roteiro em preparação" };
  if (status === "review") return { progress: 40, department: "Roteiro → Sua revisão", note: "Primeiro gate humano; nada publicado" };
  if (status === "media_queued") return { progress: 50, department: "Fila → Audio + Image + Video", note: "Pré-produção MOCK autorizada" };
  if (status === "media_production") return { progress: 75, department: "Departamentos de mídia", note: "Planos técnicos em preparação" };
  if (status === "media_review") return { progress: 100, department: "Pré-produção → Sua revisão", note: "Planos prontos; arquivos reais não gerados" };
  return { progress: 0, department: "Produção bloqueada", note: "Requer correção" };
}

function ChannelsView({ publications, busy, onPrepareEditorial, onApprove, onRetry }: { publications: TelegramPublication[]; busy: string | null; onPrepareEditorial: () => void; onApprove: (requestId: string) => void; onRetry: (requestId: string) => void }) {
  return <section className={styles.pageSection}>
    <SectionHead kicker="MARCAS E DESTINOS" title="Canais da fábrica" />
    <div className={styles.channelGrid}>
      <Channel image="/brands/fase-nova-games.png" name="Fase Nova Games" meta="TikTok + YouTube" state="Preparando conteúdo" tone="cyan" description="Notícias, lançamentos e oportunidades editoriais de games." />
      <Channel image="/brands/achados-baratos.png" name="Achados Baratos BR" meta="Facebook + Instagram" state="Orgânico conectado" tone="green" description="Curadoria de produtos, ofertas e links afiliados aprovados." />
      <Channel name="Telegram" meta="@achadosbaratosBrasil" state="Publicação controlada" tone="green" description="Primeiro canal real: prévia exata, aprovação humana, envio único e confirmação por message_id." />
      <Channel name="Shopee Afiliados" meta="Cadastro pendente" state="Aguardando telefone" tone="amber" description="Pesquisa pública é possível; comissão depende do onboarding." />
    </div>
    <div className={styles.channelPublicationPanel}>
      <SectionHead kicker="PUBLICAÇÃO CONTROLADA" title="Candidatos do Telegram" action={<button className={styles.prepareCampaign} disabled={busy === "telegram-editorial"} onClick={onPrepareEditorial}><PackagePlus size={15} /> {busy === "telegram-editorial" ? "Preparando..." : "Preparar boas-vindas"}</button>} />
      <p>Preparar cria apenas um registro local pendente. Aprovar coloca na fila local. O envio real depende de worker opt-in separado.</p>
      {publications.length ? publications.map((publication) => <TelegramPublicationStatus key={publication.id} publication={publication} busy={busy} onApprove={onApprove} onRetry={onRetry} />) : <div className={styles.empty}>Nenhum candidato preparado. Nada foi enviado ao Telegram.</div>}
    </div>
    <div className={styles.explainerBand}><Sparkles size={20} /><div><strong>Novos canais não serão criados por impulso</strong><p>Quando o radar encontrar um nicho recorrente e forte, a fábrica propõe marca, público, formato e rotina antes de você abrir uma nova conta.</p></div></div>
  </section>;
}

function ActivityView({ activity }: { activity: DashboardPayload["activity"] }) {
  return <section className={styles.historyLayout}>
    <div className={styles.activityPanel}><SectionHead kicker="REGISTRO OPERACIONAL" title="Atividade recente" />{activity.map((item) => <div className={styles.activityRow} key={item.id}><span className={`${styles.activityDot} ${styles[item.tone]}`} /><div><strong>{item.label}</strong><small>{item.detail}</small></div><time>{item.time}</time></div>)}</div>
    <div className={styles.healthPanel}><SectionHead kicker="SAÚDE TÉCNICA" title="Por que existem 119 demonstrações?" /><div className={styles.healthValue}>119/119</div><p>São cenários automáticos do sistema, não trabalhos dos funcionários. Juntos, eles executaram 1.935 verificações explícitas sobre departamentos, aprovações, custos e adapters.</p><span><Check size={16} /> Nenhuma falha na última regressão</span></div>
  </section>;
}

function SettingsView({ theme, onTheme }: { theme: Theme; onTheme: (theme: Theme) => void }) {
  return <section className={styles.settingsLayout}>
    <div className={styles.themePanel}><SectionHead kicker="APARÊNCIA" title="Tema do painel" /><div className={styles.themeChoices}><button className={theme === "operational" ? styles.themeSelected : ""} onClick={() => onTheme("operational")}><span className={styles.operationalPreview}><i /><i /><i /></span><strong>Operacional</strong><small>Discreto, limpo e focado em leitura.</small></button><button className={theme === "matrix" ? styles.themeSelected : ""} onClick={() => onTheme("matrix")}><span className={styles.matrixPreview}>0101<br />1010</span><strong>Matrix</strong><small>Preto, verde intenso e código em movimento.</small></button></div></div>
    <div className={styles.costPanel}><SectionHead kicker="PROVIDERS E ORÇAMENTO" title="APIs e custos" action={<span className={styles.safeMode}><ShieldCheck size={14} /> MOCK seguro</span>} /><div className={styles.budgetLine}><span>Gasto no ciclo atual</span><strong>R$ 0,00</strong></div><div className={styles.budgetBar}><span /></div><div className={styles.providerList}><span>Kokoro <b>Local</b></span><span>ElevenLabs <b className={styles.warningText}>Pausado</b></span><span>Telegram <b>Pronto</b></span></div></div>
    <div className={styles.safetyPanel}><SectionHead kicker="PROTEÇÕES" title="Gates obrigatórios" /><ul><li><Check size={16} /> Aprovar pauta não publica conteúdo.</li><li><Check size={16} /> Provider pago exige orçamento e aprovação.</li><li><Check size={16} /> Anúncio e publicação permanecem separados.</li></ul></div>
  </section>;
}

function NavButton({ icon, label, badge, active, onClick, className = "" }: { icon: ReactNode; label: string; badge?: number; active: boolean; onClick: () => void; className?: string }) {
  return <button className={`${styles.navButton} ${active ? styles.activeNav : ""} ${className}`} onClick={onClick}>{icon}{label}{badge !== undefined && <span>{badge}</span>}</button>;
}

function SectionHead({ kicker, title, action }: { kicker: string; title: string; action?: ReactNode }) {
  return <div className={styles.sectionHead}><div><p className={styles.kicker}>{kicker}</p><h2>{title}</h2></div>{action}</div>;
}

function Metric({ label, value, detail, icon, tone, onClick }: { label: string; value: number; detail: string; icon: ReactNode; tone: string; onClick: () => void }) {
  return <button className={`${styles.metric} ${styles[tone]}`} onClick={onClick} aria-label={`${label}: ${value}. Abrir itens`}><div className={styles.metricIcon}>{icon}</div><div className={styles.metricContent}><span className={styles.metricLabel}>{label}</span><div className={styles.metricSummary}><strong>{value}</strong><small>{detail}</small></div></div><ChevronRight className={styles.metricArrow} size={16} /></button>;
}

function marketplaceFromUrl(value: string) {
  try {
    const host = new URL(value).hostname.toLowerCase();
    if (host === "amazon.com.br" || host.endsWith(".amazon.com.br")) return "Amazon Brasil";
    if (host === "mercadolivre.com.br" || host.endsWith(".mercadolivre.com.br") || host === "mercadolivre.com" || host.endsWith(".mercadolivre.com") || host === "meli.la" || host.endsWith(".meli.la")) return "Mercado Livre";
    if (host === "shopee.com.br" || host.endsWith(".shopee.com.br")) return "Shopee";
    if (host === "adidas.com.br" || host.endsWith(".adidas.com.br")) return "Adidas";
    if (host === "digistore24.com" || host.endsWith(".digistore24.com") || host === "digistore24-app.com" || host.endsWith(".digistore24-app.com")) return "Digistore24";
    if (host === "braip.com" || host.endsWith(".braip.com") || host === "ev.braip.com" || host.endsWith(".ev.braip.com")) return "Braip";
  } catch {
    return "";
  }
  return "";
}

function isMeliShortUrl(value: string) {
  try {
    const host = new URL(value).hostname.toLowerCase();
    return host === "meli.la" || host.endsWith(".meli.la");
  } catch {
    return false;
  }
}

function isGenericMarketplaceSource(value: string) {
  try {
    const url = new URL(value);
    const host = url.hostname.toLowerCase();
    const path = url.pathname.replace(/\/+$/, "");
    return (host === "mercadolivre.com.br" || host === "www.mercadolivre.com.br") && path === "";
  } catch {
    return true;
  }
}

function mercadoLivreSearchUrl(productName: string) {
  const query = productName.normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/[^a-zA-Z0-9]+/g, "-").replace(/^-|-$/g, "").toLowerCase();
  return `https://lista.mercadolivre.com.br/${query}`;
}

function Status({ status }: { status: OpportunityStatus }) {
  return <span className={`${styles.status} ${styles[status]}`}><i />{statusLabel[status]}</span>;
}

function PipelineRow({ icon, title, department, progress, tone, note, selected, onClick }: { icon: ReactNode; title: string; department: string; progress: number; tone: string; note: string; selected: boolean; onClick: () => void }) {
  return <button type="button" className={`${styles.pipelineRow} ${selected ? styles.pipelineSelected : ""}`} onClick={onClick}><span className={`${styles.pipelineIcon} ${styles[tone]}`}>{icon}</span><div className={styles.pipelineBody}><div><strong>{title}</strong><small>{department}</small></div><div className={styles.progress}><span style={{ width: `${progress}%` }} /></div><p>{note}</p></div><b>{progress}%</b><ChevronRight className={styles.pipelineChevron} size={16} /></button>;
}

function Channel({ image, name, meta, state, tone, description }: { image?: string; name: string; meta: string; state: string; tone: string; description: string }) {
  return <article className={styles.channelCard}>{image ? <Image unoptimized src={image} alt={`Logo ${name}`} width={56} height={56} /> : <span className={styles.channelFallback}><Send size={21} /></span>}<div className={styles.channelTitle}><div><strong>{name}</strong><small>{meta}</small></div><span className={`${styles.channelState} ${styles[tone]}`}>{state}</span></div><p>{description}</p></article>;
}

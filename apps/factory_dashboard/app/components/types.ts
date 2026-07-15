export type OpportunityStatus = "pending" | "approved" | "production" | "review" | "blocked";

export type SourceReference = {
  id: string;
  label: string;
  url: string;
  sourceType: "official" | "marketplace" | "reference";
  publishedAt?: string | null;
};

export type Opportunity = {
  id: string;
  title: string;
  source: string;
  channel: string;
  category: string;
  summary: string;
  status: OpportunityStatus;
  priority: "high" | "medium" | "low";
  score: number;
  confidence: number;
  risk: string;
  nextAction: string;
  updatedAt: string;
  sources: SourceReference[];
};

export type DashboardPayload = {
  opportunities: Opportunity[];
  productions: ProductionRequest[];
  metrics: {
    pending: number;
    inProduction: number;
    ready: number;
    blocked: number;
  };
  activity: Array<{ id: string; label: string; detail: string; time: string; tone: string }>;
};

export type ProductionRequest = {
  id: string;
  opportunityId: string;
  title: string;
  channel: string;
  category: string;
  status: "queued" | "production" | "review" | "media_queued" | "media_production" | "media_review" | "failed";
  mode: "MOCK";
  hook: string;
  script: string;
  callToAction: string;
  assetPlan: string[];
  reviewNotes: string;
  publicationStatus: "blocked";
  updatedAt: string;
  sources: SourceReference[];
  media: null | {
    status: "queued" | "production" | "review" | "failed";
    reviewNotes: string;
    qualityPassed: boolean;
    providerStatus: "not_called" | "planned_not_called";
    finalAssetStatus: "not_generated";
    publicationStatus: "blocked";
    departments: Record<"audio" | "image" | "video", { label: string; status: string; summary: string; qualityPassed: boolean }>;
    providerPlans: ProviderPlan[];
    selectedProviderPlan: "local_free" | "hybrid_quality" | null;
    providerExecutionStatus: "blocked";
  };
};

export type ProviderPlan = {
  planId: "local_free" | "hybrid_quality";
  displayName: string;
  estimatedDurationSeconds: number;
  estimatedCostUsd: number;
  completePrice: boolean;
  executableNow: boolean;
  items: Array<{ department: string; provider: string; displayName: string; available: boolean; estimatedCostUsd: number; limitation: string }>;
  warning: string;
};

export type ProductIntakeStatus = "queued" | "analyzing" | "completed" | "needs_input" | "blocked";

export type CampaignPackage = {
  status: "draft_ready" | "blocked";
  product: string;
  promise: string;
  creative: string;
  channel: string;
  copy: string;
  risk: string;
  estimatedCost: string;
  missingToPublish: string[];
  publicationStatus: "blocked";
  generatedAt: string;
  organicBrief?: OrganicCampaignBrief;
};

export type OrganicCampaignBrief = {
  status: "ready_for_owner_review" | "blocked";
  goal: string;
  audience: string;
  angle: string;
  format: string;
  channel: string;
  draftCopy: string;
  disclosure: string;
  productionChecklist: string[];
  metricsToCollect: string[];
  missingBeforeProduction: string[];
  providerStatus: "not_called";
  publicationStatus: "blocked";
  generatedAt: string;
};

export type ProductIntakeItem = {
  id: string;
  productUrl: string;
  evidenceUrl: string;
  language: string;
  sourceKind: string;
  ownerNotes: string;
  targetChannel: string;
  trackingLabel: string;
  channelRegistered: boolean;
  affiliateProvided: boolean;
  marketplace: string;
  status: ProductIntakeStatus;
  productName: string;
  imageUrl: string;
  analysisSummary: string;
  promiseReview: string;
  creativeRecommendation: string;
  commissionNotes: string;
  funnelSuggestion: string;
  affiliateReadiness: string;
  campaignPackage: CampaignPackage | null;
  missingFields: string[];
  submittedAt: string;
  updatedAt: string;
};

export type ProductIntakePayload = { items: ProductIntakeItem[] };

export type ProductResearchCandidate = {
  candidate_id: string;
  product_name: string;
  marketplace: string;
  source_url: string;
  image_url: string;
  current_price: number;
  old_price: number | null;
  discount_percent: number;
  score_total: number;
  recommendation: string;
  reasons: string[];
  risk_flags: string[];
};

export type ProductResearchMissionItem = {
  id: string;
  goal: string;
  marketplaces: string[];
  category: string;
  maxPrice: number | null;
  timeframe: string;
  resultLimit: number;
  targetChannel: string;
  status: "queued" | "researching" | "review" | "needs_input" | "blocked";
  result: { shortlisted?: ProductResearchCandidate[]; next_actions?: string[]; total_candidates?: number };
  error: string;
  providerStatus: "not_called";
  publicationStatus: "blocked";
  createdAt: string;
  updatedAt: string;
};

export type ProductResearchMissionPayload = { missions: ProductResearchMissionItem[] };

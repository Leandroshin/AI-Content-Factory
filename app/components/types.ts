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
};

export type ProductIntakeItem = {
  id: string;
  productUrl: string;
  evidenceUrl: string;
  language: string;
  sourceKind: string;
  ownerNotes: string;
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

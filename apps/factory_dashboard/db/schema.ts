import { integer, sqliteTable, text } from "drizzle-orm/sqlite-core";

export const opportunities = sqliteTable("opportunities", {
  id: text("id").primaryKey(),
  title: text("title").notNull(),
  source: text("source").notNull(),
  channel: text("channel").notNull(),
  category: text("category").notNull(),
  summary: text("summary").notNull(),
  status: text("status").notNull(),
  priority: text("priority").notNull(),
  score: integer("score").notNull(),
  confidence: integer("confidence").notNull(),
  risk: text("risk").notNull(),
  nextAction: text("next_action").notNull(),
  updatedAt: text("updated_at").notNull(),
});

export const activityLog = sqliteTable("activity_log", {
  id: text("id").primaryKey(),
  label: text("label").notNull(),
  detail: text("detail").notNull(),
  tone: text("tone").notNull(),
  createdAt: text("created_at").notNull(),
});

export const opportunitySources = sqliteTable("opportunity_sources", {
  id: text("id").primaryKey(),
  opportunityId: text("opportunity_id").notNull(),
  label: text("label").notNull(),
  url: text("url").notNull(),
  sourceType: text("source_type").notNull(),
  publishedAt: text("published_at"),
});

export const productIntakeRequests = sqliteTable("product_intake_requests", {
  id: text("id").primaryKey(),
  productUrl: text("product_url").notNull(),
  affiliateUrl: text("affiliate_url").notNull(),
  evidenceUrl: text("evidence_url"),
  language: text("language"),
  sourceKind: text("source_kind"),
  ownerNotes: text("owner_notes"),
  marketplace: text("marketplace").notNull(),
  status: text("status").notNull(),
  productName: text("product_name").notNull(),
  imageUrl: text("image_url").notNull(),
  analysisSummary: text("analysis_summary").notNull(),
  promiseReview: text("promise_review"),
  creativeRecommendation: text("creative_recommendation"),
  commissionNotes: text("commission_notes"),
  funnelSuggestion: text("funnel_suggestion"),
  affiliateReadiness: text("affiliate_readiness"),
  missingFields: text("missing_fields").notNull(),
  submittedAt: text("submitted_at").notNull(),
  updatedAt: text("updated_at").notNull(),
});

export const productionRequests = sqliteTable("production_requests", {
  id: text("id").primaryKey(),
  opportunityId: text("opportunity_id").notNull().unique(),
  status: text("status").notNull(),
  mode: text("mode").notNull(),
  hook: text("hook").notNull(),
  script: text("script").notNull(),
  callToAction: text("call_to_action").notNull(),
  assetPlan: text("asset_plan").notNull(),
  reviewNotes: text("review_notes").notNull(),
  publicationStatus: text("publication_status").notNull(),
  createdAt: text("created_at").notNull(),
  updatedAt: text("updated_at").notNull(),
});

export const mediaProductionRequests = sqliteTable("media_production_requests", {
  id: text("id").primaryKey(),
  opportunityId: text("opportunity_id").notNull().unique(),
  status: text("status").notNull(),
  mode: text("mode").notNull(),
  departments: text("departments").notNull(),
  reviewNotes: text("review_notes").notNull(),
  qualityPassed: integer("quality_passed").notNull(),
  providerStatus: text("provider_status").notNull(),
  finalAssetStatus: text("final_asset_status").notNull(),
  publicationStatus: text("publication_status").notNull(),
  createdAt: text("created_at").notNull(),
  updatedAt: text("updated_at").notNull(),
});

export const providerPlanSelections = sqliteTable("provider_plan_selections", {
  id: text("id").primaryKey(),
  opportunityId: text("opportunity_id").notNull().unique(),
  planId: text("plan_id").notNull(),
  quoteSnapshot: text("quote_snapshot").notNull(),
  estimatedCostUsd: integer("estimated_cost_usd_cents").notNull(),
  pricingComplete: integer("pricing_complete").notNull(),
  executionStatus: text("execution_status").notNull(),
  ownerApprovedExecution: integer("owner_approved_execution").notNull(),
  createdAt: text("created_at").notNull(),
  updatedAt: text("updated_at").notNull(),
});

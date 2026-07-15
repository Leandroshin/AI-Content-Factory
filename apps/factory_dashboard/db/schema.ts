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
  targetChannel: text("target_channel").notNull(),
  trackingLabel: text("tracking_label").notNull(),
  channelRegistered: integer("channel_registered").notNull(),
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
  campaignPackage: text("campaign_package"),
  currentPriceCents: integer("current_price_cents"),
  oldPriceCents: integer("old_price_cents"),
  commissionConfirmed: integer("commission_confirmed").notNull().default(0),
  creativeReviewStatus: text("creative_review_status").notNull().default(""),
  missingFields: text("missing_fields").notNull(),
  submittedAt: text("submitted_at").notNull(),
  updatedAt: text("updated_at").notNull(),
});

export const telegramPublicationRequests = sqliteTable("telegram_publication_requests", {
  id: text("id").primaryKey(),
  productId: text("product_id").notNull(),
  status: text("status").notNull(),
  chatId: text("chat_id").notNull(),
  messageText: text("message_text").notNull(),
  affiliateUrl: text("affiliate_url").notNull(),
  imageUrl: text("image_url").notNull(),
  ownerApproved: integer("owner_approved").notNull(),
  linkPreviewEnabled: integer("link_preview_enabled").notNull(),
  telegramMessageId: integer("telegram_message_id"),
  error: text("error").notNull(),
  approvedAt: text("approved_at").notNull(),
  claimedAt: text("claimed_at"),
  sentAt: text("sent_at"),
  createdAt: text("created_at").notNull(),
  updatedAt: text("updated_at").notNull(),
});

export const productResearchMissions = sqliteTable("product_research_missions", {
  id: text("id").primaryKey(),
  goal: text("goal").notNull(),
  marketplaces: text("marketplaces").notNull(),
  category: text("category").notNull(),
  maxPriceCents: integer("max_price_cents"),
  timeframe: text("timeframe").notNull(),
  resultLimit: integer("result_limit").notNull(),
  targetChannel: text("target_channel").notNull(),
  status: text("status").notNull(),
  result: text("result").notNull(),
  error: text("error").notNull(),
  createdAt: text("created_at").notNull(),
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

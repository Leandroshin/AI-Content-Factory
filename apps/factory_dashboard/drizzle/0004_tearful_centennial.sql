CREATE TABLE `media_production_requests` (
	`id` text PRIMARY KEY NOT NULL,
	`opportunity_id` text NOT NULL,
	`status` text NOT NULL,
	`mode` text NOT NULL,
	`departments` text NOT NULL,
	`review_notes` text NOT NULL,
	`quality_passed` integer NOT NULL,
	`provider_status` text NOT NULL,
	`final_asset_status` text NOT NULL,
	`publication_status` text NOT NULL,
	`created_at` text NOT NULL,
	`updated_at` text NOT NULL
);
--> statement-breakpoint
CREATE UNIQUE INDEX `media_production_requests_opportunity_id_unique` ON `media_production_requests` (`opportunity_id`);--> statement-breakpoint
CREATE TABLE `provider_plan_selections` (
	`id` text PRIMARY KEY NOT NULL,
	`opportunity_id` text NOT NULL,
	`plan_id` text NOT NULL,
	`quote_snapshot` text NOT NULL,
	`estimated_cost_usd_cents` integer NOT NULL,
	`pricing_complete` integer NOT NULL,
	`execution_status` text NOT NULL,
	`owner_approved_execution` integer NOT NULL,
	`created_at` text NOT NULL,
	`updated_at` text NOT NULL
);
--> statement-breakpoint
CREATE UNIQUE INDEX `provider_plan_selections_opportunity_id_unique` ON `provider_plan_selections` (`opportunity_id`);--> statement-breakpoint
ALTER TABLE `product_intake_requests` ADD `evidence_url` text;--> statement-breakpoint
ALTER TABLE `product_intake_requests` ADD `language` text;--> statement-breakpoint
ALTER TABLE `product_intake_requests` ADD `source_kind` text;--> statement-breakpoint
ALTER TABLE `product_intake_requests` ADD `owner_notes` text;--> statement-breakpoint
ALTER TABLE `product_intake_requests` ADD `promise_review` text;--> statement-breakpoint
ALTER TABLE `product_intake_requests` ADD `creative_recommendation` text;--> statement-breakpoint
ALTER TABLE `product_intake_requests` ADD `commission_notes` text;--> statement-breakpoint
ALTER TABLE `product_intake_requests` ADD `funnel_suggestion` text;--> statement-breakpoint
ALTER TABLE `product_intake_requests` ADD `affiliate_readiness` text;--> statement-breakpoint
ALTER TABLE `product_intake_requests` ADD `campaign_package` text;
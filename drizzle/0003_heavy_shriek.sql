CREATE TABLE `production_requests` (
	`id` text PRIMARY KEY NOT NULL,
	`opportunity_id` text NOT NULL,
	`status` text NOT NULL,
	`mode` text NOT NULL,
	`hook` text NOT NULL,
	`script` text NOT NULL,
	`call_to_action` text NOT NULL,
	`asset_plan` text NOT NULL,
	`review_notes` text NOT NULL,
	`publication_status` text NOT NULL,
	`created_at` text NOT NULL,
	`updated_at` text NOT NULL
);
--> statement-breakpoint
CREATE UNIQUE INDEX `production_requests_opportunity_id_unique` ON `production_requests` (`opportunity_id`);
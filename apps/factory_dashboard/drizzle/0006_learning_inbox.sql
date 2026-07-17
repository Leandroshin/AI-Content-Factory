CREATE TABLE `learning_source_requests` (
	`id` text PRIMARY KEY NOT NULL,
	`source_url` text NOT NULL,
	`canonical_url` text NOT NULL,
	`external_id` text NOT NULL,
	`platform` text NOT NULL,
	`title` text NOT NULL,
	`owner_notes` text NOT NULL,
	`language` text NOT NULL,
	`status` text NOT NULL,
	`transcript_status` text NOT NULL,
	`transcript` text NOT NULL,
	`transcript_hash` text NOT NULL,
	`evidence_status` text NOT NULL,
	`audit_status` text NOT NULL,
	`experiment_status` text NOT NULL,
	`knowledge_status` text NOT NULL,
	`provider_status` text NOT NULL,
	`publication_status` text NOT NULL,
	`estimated_cost_usd_cents` integer NOT NULL,
	`missing_requirements` text NOT NULL,
	`submitted_at` text NOT NULL,
	`updated_at` text NOT NULL
);
--> statement-breakpoint
CREATE UNIQUE INDEX `learning_source_requests_source_url_unique` ON `learning_source_requests` (`source_url`);
--> statement-breakpoint
CREATE UNIQUE INDEX `learning_source_requests_canonical_url_unique` ON `learning_source_requests` (`canonical_url`);
--> statement-breakpoint
CREATE UNIQUE INDEX `learning_source_requests_external_id_unique` ON `learning_source_requests` (`external_id`);

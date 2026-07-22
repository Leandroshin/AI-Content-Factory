ALTER TABLE `telegram_publication_requests` ADD `authorization_kind` text DEFAULT 'manual' NOT NULL;
--> statement-breakpoint
ALTER TABLE `telegram_publication_requests` ADD `policy_id` text DEFAULT '' NOT NULL;
--> statement-breakpoint
ALTER TABLE `telegram_publication_requests` ADD `policy_version` integer DEFAULT 0 NOT NULL;
--> statement-breakpoint
ALTER TABLE `telegram_publication_requests` ADD `idempotency_key` text DEFAULT '' NOT NULL;
--> statement-breakpoint
ALTER TABLE `telegram_publication_requests` ADD `content_hash` text DEFAULT '' NOT NULL;
--> statement-breakpoint
ALTER TABLE `telegram_publication_requests` ADD `validation_snapshot_hash` text DEFAULT '' NOT NULL;
--> statement-breakpoint
ALTER TABLE `telegram_publication_requests` ADD `lease_token` text DEFAULT '' NOT NULL;
--> statement-breakpoint
ALTER TABLE `telegram_publication_requests` ADD `lease_expires_at` text DEFAULT '' NOT NULL;
--> statement-breakpoint
CREATE TABLE `telegram_autopilot_policies` (
	`id` text PRIMARY KEY NOT NULL,
	`status` text NOT NULL,
	`version` integer DEFAULT 1 NOT NULL,
	`chat_id` text NOT NULL,
	`max_publications_per_day` integer DEFAULT 48 NOT NULL,
	`sent_today` integer DEFAULT 0 NOT NULL,
	`failed_today` integer DEFAULT 0 NOT NULL,
	`reserved_today` integer DEFAULT 0 NOT NULL,
	`day_key` text NOT NULL,
	`min_interval_minutes` integer DEFAULT 30 NOT NULL,
	`next_run_at` text DEFAULT '' NOT NULL,
	`last_reserved_at` text DEFAULT '' NOT NULL,
	`last_sent_at` text DEFAULT '' NOT NULL,
	`allowed_marketplaces` text DEFAULT '["Mercado Livre"]' NOT NULL,
	`owner_confirmation` text DEFAULT '' NOT NULL,
	`created_at` text NOT NULL,
	`updated_at` text NOT NULL
);
--> statement-breakpoint
CREATE INDEX `telegram_autopilot_status_idx` ON `telegram_autopilot_policies` (`status`);
--> statement-breakpoint
CREATE UNIQUE INDEX `telegram_publication_idempotency_idx` ON `telegram_publication_requests` (`idempotency_key`) WHERE `idempotency_key` <> '';

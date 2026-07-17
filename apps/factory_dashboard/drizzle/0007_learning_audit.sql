ALTER TABLE `learning_source_requests` ADD `audit_packet` text DEFAULT '{}' NOT NULL;
--> statement-breakpoint
ALTER TABLE `learning_source_requests` ADD `audit_submitted_at` text DEFAULT '' NOT NULL;

CREATE TABLE IF NOT EXISTS `telegram_publication_requests` (
	`id` text PRIMARY KEY NOT NULL,
	`product_id` text NOT NULL,
	`status` text NOT NULL,
	`chat_id` text NOT NULL,
	`message_text` text NOT NULL,
	`affiliate_url` text NOT NULL,
	`image_url` text NOT NULL,
	`owner_approved` integer NOT NULL,
	`link_preview_enabled` integer NOT NULL,
	`telegram_message_id` integer,
	`error` text NOT NULL,
	`approved_at` text NOT NULL,
	`claimed_at` text,
	`sent_at` text,
	`created_at` text NOT NULL,
	`updated_at` text NOT NULL
);
--> statement-breakpoint
ALTER TABLE `product_intake_requests` ADD `current_price_cents` integer;--> statement-breakpoint
ALTER TABLE `product_intake_requests` ADD `old_price_cents` integer;--> statement-breakpoint
ALTER TABLE `product_intake_requests` ADD `commission_confirmed` integer DEFAULT 0 NOT NULL;--> statement-breakpoint
ALTER TABLE `product_intake_requests` ADD `creative_review_status` text DEFAULT '' NOT NULL;

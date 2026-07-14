CREATE TABLE `product_research_missions` (
	`id` text PRIMARY KEY NOT NULL,
	`goal` text NOT NULL,
	`marketplaces` text NOT NULL,
	`category` text NOT NULL,
	`max_price_cents` integer,
	`timeframe` text NOT NULL,
	`result_limit` integer NOT NULL,
	`target_channel` text NOT NULL,
	`status` text NOT NULL,
	`result` text NOT NULL,
	`error` text NOT NULL,
	`created_at` text NOT NULL,
	`updated_at` text NOT NULL
);

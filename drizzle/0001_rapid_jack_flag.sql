CREATE TABLE `opportunity_sources` (
	`id` text PRIMARY KEY NOT NULL,
	`opportunity_id` text NOT NULL,
	`label` text NOT NULL,
	`url` text NOT NULL,
	`source_type` text NOT NULL,
	`published_at` text
);

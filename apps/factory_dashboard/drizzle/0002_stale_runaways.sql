CREATE TABLE `product_intake_requests` (
	`id` text PRIMARY KEY NOT NULL,
	`product_url` text NOT NULL,
	`affiliate_url` text NOT NULL,
	`marketplace` text NOT NULL,
	`status` text NOT NULL,
	`product_name` text NOT NULL,
	`image_url` text NOT NULL,
	`analysis_summary` text NOT NULL,
	`missing_fields` text NOT NULL,
	`submitted_at` text NOT NULL,
	`updated_at` text NOT NULL
);

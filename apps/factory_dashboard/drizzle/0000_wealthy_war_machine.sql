CREATE TABLE `activity_log` (
	`id` text PRIMARY KEY NOT NULL,
	`label` text NOT NULL,
	`detail` text NOT NULL,
	`tone` text NOT NULL,
	`created_at` text NOT NULL
);
--> statement-breakpoint
CREATE TABLE `opportunities` (
	`id` text PRIMARY KEY NOT NULL,
	`title` text NOT NULL,
	`source` text NOT NULL,
	`channel` text NOT NULL,
	`category` text NOT NULL,
	`summary` text NOT NULL,
	`status` text NOT NULL,
	`priority` text NOT NULL,
	`score` integer NOT NULL,
	`confidence` integer NOT NULL,
	`risk` text NOT NULL,
	`next_action` text NOT NULL,
	`updated_at` text NOT NULL
);

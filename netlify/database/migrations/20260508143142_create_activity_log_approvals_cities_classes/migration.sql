CREATE TABLE "activity_log" (
	"id" serial PRIMARY KEY,
	"action_type" text NOT NULL,
	"description" text NOT NULL,
	"user_name" text,
	"timestamp" timestamp DEFAULT now()
);
--> statement-breakpoint
CREATE TABLE "approvals" (
	"id" serial PRIMARY KEY,
	"student_id" integer NOT NULL,
	"class_id" integer NOT NULL,
	"task_id" integer NOT NULL,
	"grade_points" integer NOT NULL,
	"mentor_signature" text NOT NULL,
	"approval_date" date NOT NULL,
	"notes" text,
	"created_at" timestamp DEFAULT now()
);
--> statement-breakpoint
CREATE TABLE "cities" (
	"id" serial PRIMARY KEY,
	"name" text NOT NULL UNIQUE,
	"created_at" timestamp DEFAULT now()
);
--> statement-breakpoint
CREATE TABLE "classes" (
	"id" serial PRIMARY KEY,
	"city_id" integer NOT NULL,
	"name" text NOT NULL,
	"created_at" timestamp DEFAULT now(),
	CONSTRAINT "classes_city_id_name_unique" UNIQUE("city_id","name")
);
--> statement-breakpoint
CREATE TABLE "students" (
	"id" serial PRIMARY KEY,
	"name" text NOT NULL,
	"city_id" integer NOT NULL,
	"class_id" integer,
	"total_points" integer DEFAULT 0,
	"created_at" timestamp DEFAULT now(),
	CONSTRAINT "students_name_city_id_unique" UNIQUE("name","city_id")
);
--> statement-breakpoint
CREATE TABLE "tasks" (
	"id" serial PRIMARY KEY,
	"class_id" integer NOT NULL,
	"task_name" text NOT NULL,
	"max_points" integer DEFAULT 100,
	CONSTRAINT "tasks_class_id_task_name_unique" UNIQUE("class_id","task_name")
);
--> statement-breakpoint
ALTER TABLE "approvals" ADD CONSTRAINT "approvals_student_id_students_id_fkey" FOREIGN KEY ("student_id") REFERENCES "students"("id");--> statement-breakpoint
ALTER TABLE "approvals" ADD CONSTRAINT "approvals_class_id_classes_id_fkey" FOREIGN KEY ("class_id") REFERENCES "classes"("id");--> statement-breakpoint
ALTER TABLE "approvals" ADD CONSTRAINT "approvals_task_id_tasks_id_fkey" FOREIGN KEY ("task_id") REFERENCES "tasks"("id");--> statement-breakpoint
ALTER TABLE "classes" ADD CONSTRAINT "classes_city_id_cities_id_fkey" FOREIGN KEY ("city_id") REFERENCES "cities"("id");--> statement-breakpoint
ALTER TABLE "students" ADD CONSTRAINT "students_city_id_cities_id_fkey" FOREIGN KEY ("city_id") REFERENCES "cities"("id");--> statement-breakpoint
ALTER TABLE "students" ADD CONSTRAINT "students_class_id_classes_id_fkey" FOREIGN KEY ("class_id") REFERENCES "classes"("id");--> statement-breakpoint
ALTER TABLE "tasks" ADD CONSTRAINT "tasks_class_id_classes_id_fkey" FOREIGN KEY ("class_id") REFERENCES "classes"("id") ON DELETE CASCADE;
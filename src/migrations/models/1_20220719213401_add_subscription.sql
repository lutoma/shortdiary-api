-- upgrade --
CREATE TABLE IF NOT EXISTS "subscription" (
    "id" UUID NOT NULL  PRIMARY KEY,
    "plan" VARCHAR(100) NOT NULL,
    "plan_name" VARCHAR(500) NOT NULL,
    "last_changed" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "start_time" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "end_time" TIMESTAMPTZ,
    "user_id" UUID NOT NULL UNIQUE REFERENCES "user" ("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "idx_subscriptio_user_id_3417ce" ON "subscription" ("user_id");;
ALTER TABLE "user" ADD "stripe_id" VARCHAR(255);
ALTER TABLE "user" ADD "stripe_intent_id" VARCHAR(255);
-- downgrade --
ALTER TABLE "user" DROP COLUMN "stripe_id";
ALTER TABLE "user" DROP COLUMN "stripe_intent_id";
DROP TABLE IF EXISTS "subscription";

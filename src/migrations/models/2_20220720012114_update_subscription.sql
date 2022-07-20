-- upgrade --
ALTER TABLE "subscription" ADD "stripe_id" VARCHAR(255);
ALTER TABLE "subscription" ADD "active" BOOL NOT NULL;
ALTER TABLE "user" DROP COLUMN "stripe_intent_id";
-- downgrade --
ALTER TABLE "user" ADD "stripe_intent_id" VARCHAR(255);
ALTER TABLE "subscription" DROP COLUMN "stripe_id";
ALTER TABLE "subscription" DROP COLUMN "active";

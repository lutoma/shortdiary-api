-- upgrade --
ALTER TABLE "subscription" ADD "status" VARCHAR(255) NOT NULL;
ALTER TABLE "subscription" DROP COLUMN "active";
CREATE INDEX "idx_subscriptio_stripe__1af1ac" ON "subscription" ("stripe_id");
CREATE INDEX "idx_user_stripe__d3daa5" ON "user" ("stripe_id");
-- downgrade --
DROP INDEX "idx_subscriptio_stripe__1af1ac";
DROP INDEX "idx_user_stripe__d3daa5";
ALTER TABLE "subscription" ADD "active" BOOL NOT NULL;
ALTER TABLE "subscription" DROP COLUMN "status";

-- upgrade --
CREATE TABLE IF NOT EXISTS "user" (
    "id" UUID NOT NULL  PRIMARY KEY,
    "joined" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "last_seen" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "email" VARCHAR(255) NOT NULL UNIQUE,
    "email_verified" BOOL NOT NULL  DEFAULT False,
    "ephemeral_key_salt" VARCHAR(22),
    "master_key" VARCHAR(64),
    "master_key_nonce" VARCHAR(32),
    "password" VARCHAR(100) NOT NULL,
    "legacy_username" VARCHAR(255)  UNIQUE
);
CREATE INDEX IF NOT EXISTS "idx_user_email_1b4f1c" ON "user" ("email");
CREATE TABLE IF NOT EXISTS "post" (
    "id" UUID NOT NULL  PRIMARY KEY,
    "date" DATE NOT NULL,
    "last_changed" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "created" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "format_version" INT NOT NULL  DEFAULT 1,
    "nonce" VARCHAR(32),
    "data" BYTEA NOT NULL,
    "author_id" UUID NOT NULL REFERENCES "user" ("id") ON DELETE CASCADE,
    CONSTRAINT "uid_post_author__90fab2" UNIQUE ("author_id", "date")
);
CREATE INDEX IF NOT EXISTS "idx_post_author__0da5e6" ON "post" ("author_id");
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(100) NOT NULL,
    "content" JSONB NOT NULL
);

#!/usr/bin/env bash
# Creates .env.smorx-costsheet.production and .secrets/aws/credentials on the server.
# Secrets are generated with openssl or typed in (hidden) and are never echoed.
# Safe to re-run: an existing env file is left untouched so the DB password
# keeps matching the data already in the smorx-costsheet-pgdata volume.
set -euo pipefail

cd "$(dirname "$0")/.."
umask 077

ENV_FILE=".env.smorx-costsheet.production"
AWS_DIR=".secrets/aws"
PUBLIC_HOST="${PUBLIC_HOST:-100.51.165.76}"

if [ -f "$ENV_FILE" ]; then
  echo "$ENV_FILE already exists - leaving it unchanged."
else
  DB_USER="costsheet"
  DB_NAME="costsheet"
  DB_PASS="$(openssl rand -hex 32)"

  printf "OpenAI API key for AI insights (input hidden, Enter to skip): "
  IFS= read -rs OPENAI_KEY || true
  echo

  cat > "$ENV_FILE" <<EOF
POSTGRES_USER=${DB_USER}
POSTGRES_PASSWORD=${DB_PASS}
POSTGRES_DB=${DB_NAME}
DATABASE_URL=postgresql://${DB_USER}:${DB_PASS}@db:5432/${DB_NAME}
OPENAI_API_KEY=${OPENAI_KEY}
OPENAI_MODEL=gpt-4o-mini
ALLOWED_ORIGINS=http://${PUBLIC_HOST}:28080
WEB_CONCURRENCY=2
AWS_S3_BUCKET=ieppcostsheeterp
AWS_REGION=ap-south-1
AWS_S3_PREFIX=costsheet
EOF
  unset DB_PASS OPENAI_KEY
  echo "Created $ENV_FILE (values not shown)."
  echo "Run deploy/configure-s3.smorx-costsheet.sh next to set the S3 bucket."
fi
chmod 600 "$ENV_FILE"

mkdir -p "$AWS_DIR"
chmod 700 .secrets "$AWS_DIR"
if [ ! -f "$AWS_DIR/credentials" ]; then
  touch "$AWS_DIR/credentials"
  echo "Created empty $AWS_DIR/credentials - edit it yourself with: nano $AWS_DIR/credentials"
fi
chmod 600 "$AWS_DIR/credentials"

echo "Done. Variable names in $ENV_FILE:"
cut -d= -f1 "$ENV_FILE" | sed 's/^/  /'

#!/usr/bin/env bash
# One-shot: set S3 to s3://ieppcostsheeterp/costsheet/ without touching DB secrets.
set -euo pipefail
cd "$(dirname "$0")/.."
umask 077

ENV_FILE=".env.smorx-costsheet.production"
if [ ! -f "$ENV_FILE" ]; then
  echo "Missing $ENV_FILE - run deploy/setup-env.smorx-costsheet.sh first."
  exit 1
fi

tmp="$(mktemp)"
grep -vE '^(AWS_S3_BUCKET|AWS_REGION|AWS_S3_PREFIX)=' "$ENV_FILE" > "$tmp"
cat >> "$tmp" <<'EOF'
AWS_S3_BUCKET=ieppcostsheeterp
AWS_REGION=ap-south-1
AWS_S3_PREFIX=costsheet
EOF
mv "$tmp" "$ENV_FILE"
chmod 600 "$ENV_FILE"

mkdir -p .secrets/aws
chmod 700 .secrets .secrets/aws
touch .secrets/aws/credentials
chmod 600 .secrets/aws/credentials

echo "S3 target set to s3://ieppcostsheeterp/costsheet/"
echo "If credentials are empty, edit them yourself:"
echo "  nano .secrets/aws/credentials"
echo "Then:"
echo "  docker compose -f docker-compose.smorx-costsheet.yml up -d --build api"

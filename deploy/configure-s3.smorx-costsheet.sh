#!/usr/bin/env bash
# Appends / updates S3 settings in an existing .env.smorx-costsheet.production.
# Does NOT touch DB passwords. AWS access keys go in .secrets/aws/credentials
# (typed by you; never printed here).
set -euo pipefail

cd "$(dirname "$0")/.."
umask 077

ENV_FILE=".env.smorx-costsheet.production"
AWS_CREDS=".secrets/aws/credentials"

if [ ! -f "$ENV_FILE" ]; then
  echo "Missing $ENV_FILE - run deploy/setup-env.smorx-costsheet.sh first."
  exit 1
fi

printf "S3 bucket name [ieppcostsheeterp]: "
IFS= read -r BUCKET
BUCKET="${BUCKET:-ieppcostsheeterp}"
printf "AWS region [ap-south-1]: "
IFS= read -r REGION
REGION="${REGION:-ap-south-1}"
printf "S3 key prefix [costsheet]: "
IFS= read -r PREFIX
PREFIX="${PREFIX:-costsheet}"

tmp="$(mktemp)"
grep -vE '^(AWS_S3_BUCKET|AWS_REGION|AWS_S3_PREFIX)=' "$ENV_FILE" > "$tmp"
cat >> "$tmp" <<EOF
AWS_S3_BUCKET=${BUCKET}
AWS_REGION=${REGION}
AWS_S3_PREFIX=${PREFIX}
EOF
mv "$tmp" "$ENV_FILE"
chmod 600 "$ENV_FILE"
unset BUCKET REGION PREFIX

mkdir -p .secrets/aws
chmod 700 .secrets .secrets/aws
if [ ! -f "$AWS_CREDS" ]; then
  touch "$AWS_CREDS"
fi
chmod 600 "$AWS_CREDS"

echo
echo "Updated S3 settings in $ENV_FILE (values not shown)."
echo "Now edit the IAM credentials file yourself (input stays on the server):"
echo "  nano $AWS_CREDS"
echo
echo "Expected format:"
echo "  [default]"
echo "  aws_access_key_id = <your-key-id>"
echo "  aws_secret_access_key = <your-secret>"
echo
echo "Then rebuild the API:"
echo "  docker compose -f docker-compose.smorx-costsheet.yml up -d --build api"

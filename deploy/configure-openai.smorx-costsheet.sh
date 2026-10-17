#!/usr/bin/env bash
# Set / update OPENAI_API_KEY on an existing .env without touching DB secrets.
# Key is typed with hidden input and never printed.
set -euo pipefail

cd "$(dirname "$0")/.."
umask 077

ENV_FILE=".env.smorx-costsheet.production"
if [ ! -f "$ENV_FILE" ]; then
  echo "Missing $ENV_FILE - run deploy/setup-env.smorx-costsheet.sh first."
  exit 1
fi

printf "OpenAI API key (input hidden): "
IFS= read -rs OPENAI_KEY || true
echo
printf "OpenAI model [gpt-4o-mini]: "
IFS= read -r MODEL || true
MODEL="${MODEL:-gpt-4o-mini}"

if [ -z "$OPENAI_KEY" ]; then
  echo "Key is required."
  exit 1
fi

tmp="$(mktemp)"
grep -vE '^(OPENAI_API_KEY|OPENAI_MODEL|ANTHROPIC_API_KEY)=' "$ENV_FILE" > "$tmp"
cat >> "$tmp" <<EOF
OPENAI_API_KEY=${OPENAI_KEY}
OPENAI_MODEL=${MODEL}
EOF
mv "$tmp" "$ENV_FILE"
chmod 600 "$ENV_FILE"
unset OPENAI_KEY MODEL

echo "Updated OPENAI_API_KEY / OPENAI_MODEL in $ENV_FILE (values not shown)."
echo "Rebuild API:"
echo "  docker compose -f docker-compose.smorx-costsheet.yml up -d --build api"

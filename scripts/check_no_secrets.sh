#!/usr/bin/env bash
# Lightweight guardrail: scan git-tracked files for obvious secret patterns.
# Not a substitute for real secret scanning — just catches accidental commits.
#
# Usage:  bash scripts/check_no_secrets.sh
# Exit:   0 = clean, 1 = potential secret found.

set -u
cd "$(dirname "$0")/.." || exit 2

# Patterns that should never appear in committed source.
#  - AIza...            Google API key prefix
#  - filled-in secrets in .env-style assignments
PATTERNS='AIza[0-9A-Za-z_\-]{20,}|GEMINI_API_KEY=[^[:space:]]+|postgres(ql)?://[^[:space:]]*:[^[:space:]]*@|DEMO_ADMIN_TOKEN=[^[:space:]]+'

# Only scan tracked files, and never the example env or this script itself.
files=$(git ls-files | grep -vE '(^|/)\.env\.example$|scripts/check_no_secrets\.sh$')

# Ignore obvious placeholders (your_key_here, <token>, example, redacted, xxx...).
PLACEHOLDERS='your[_-]?key|your[_-]?token|example|redacted|placeholder|<[^>]+>|xxx+|changeme|here'

hits=$(echo "$files" | xargs -r grep -nEI "$PATTERNS" 2>/dev/null | grep -vEi "$PLACEHOLDERS")

if [ -n "$hits" ]; then
  echo "Potential secrets found in tracked files:"
  echo "$hits"
  echo
  echo "If these are placeholders, ignore. Otherwise remove them and rotate the secret."
  exit 1
fi

echo "No obvious secrets found in tracked files."
exit 0

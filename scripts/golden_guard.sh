#!/usr/bin/env bash
set -e
CHANGED=$(git diff --cached --name-only | grep '^golden/' || true)
if [ -n "$CHANGED" ] && [ -z "$UPDATE_GOLDEN" ]; then
  echo "golden files changed; set UPDATE_GOLDEN=1 to allow"
  exit 1
fi
exit 0

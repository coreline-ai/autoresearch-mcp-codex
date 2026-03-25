#!/usr/bin/env bash
set -euo pipefail

MESSAGE="${1:-accepted iteration change}"

if [[ -n "$(git status --porcelain)" ]]; then
  git add .
  git commit -m "$MESSAGE"
  echo "Accepted and committed: $MESSAGE"
else
  echo "No changes to commit."
fi

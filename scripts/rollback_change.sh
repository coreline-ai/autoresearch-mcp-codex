#!/usr/bin/env bash
set -euo pipefail

git restore .
git clean -fd
echo "Rollback completed"

#!/bin/bash
# Parse the wildcard (*) entry in .github/CODEOWNERS and write a comma-separated
# list of assignees (without the @ prefix) to GITHUB_OUTPUT.
#
# Usage: bash .github/scripts/get-codeowners-assignees.sh

CODEOWNERS_FILE=".github/CODEOWNERS"

if [ ! -f "$CODEOWNERS_FILE" ]; then
  echo "::warning::CODEOWNERS file not found at $CODEOWNERS_FILE. No assignees will be set."
  echo "assignees=" >> "$GITHUB_OUTPUT"
  exit 0
fi

owners=$(grep '^\*' "$CODEOWNERS_FILE" | sed 's/^\*[[:space:]]*//' | sed 's/@//g' | tr -s ' ' ',' | sed 's/,$//')

if [ -z "$owners" ]; then
  echo "::warning::No wildcard (*) pattern found in CODEOWNERS. No assignees will be set."
  echo "assignees=" >> "$GITHUB_OUTPUT"
  exit 0
fi

echo "assignees=$owners" >> "$GITHUB_OUTPUT"

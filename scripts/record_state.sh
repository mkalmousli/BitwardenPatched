#!/usr/bin/env bash
set -euo pipefail
git config user.name bitwarden-patched
git config user.email actions@users.noreply.github.com
for attempt in 1 2 3 4 5; do
  git fetch -q origin main
  git reset -q --hard origin/main
  python3 state.py record "$1" "$2" "$3"
  git add state.json
  if git diff --cached --quiet; then exit 0; fi
  git commit -qm "state: $1 $2 [skip ci]"
  if git push -q origin HEAD:main; then exit 0; fi
  sleep 5
done
echo 'Could not save release state after five attempts' >&2
exit 1

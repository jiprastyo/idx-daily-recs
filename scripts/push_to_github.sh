#!/bin/bash
# One-command push to GitHub. Uses the gh CLI (authed) to create the repo if missing,
# push main, enable Pages (Actions source) and trigger the first workflow run.
# No gh CLI? Falls back to printing the 4 manual steps.
# Usage: ./scripts/push_to_github.sh [repo-name]   (default repo-name: idx-daily-recs)
set -euo pipefail
cd "$(dirname "$0")/.."

echo "== 1/4 checks =="
git branch -M main 2>/dev/null || true
if [ -n "$(git status --porcelain)" ]; then
  echo "Uncommitted changes:"
  git status --short
  read -r -p "Commit them all now? [y/N] " ans
  if [ "$ans" != "y" ]; then echo "Aborting — commit or stash first."; exit 1; fi
  git add -A && git commit -q -m "chore: pre-push updates"
fi
echo "  clean, branch: $(git branch --show-current)"

REPO="${1:-idx-daily-recs}"

if ! command -v gh >/dev/null 2>&1 || ! gh auth status >/dev/null 2>&1; then
  echo
  echo "== gh CLI not available/authed — manual steps =="
  echo "  1. Create the repo at https://github.com/new  (name: $REPO, PUBLIC — Pages is free only on public repos)"
  echo "     Do NOT add a README/.gitignore (this repo already has them)."
  echo "  2. git remote add origin https://github.com/<YOU>/$REPO.git"
  echo "  3. git push -u origin main"
  echo "  4. Repo -> Settings -> Pages -> Source: 'GitHub Actions'"
  exit 0
fi

OWNER="$(gh api user -q .login)"
echo "  gh authed as: $OWNER"

echo "== 2/4 remote =="
if ! git remote get-url origin >/dev/null 2>&1; then
  if gh repo view "$OWNER/$REPO" >/dev/null 2>&1; then
    echo "  repo exists on GitHub — adding remote"
    git remote add origin "https://github.com/$OWNER/$REPO.git"
  else
    echo "  creating public repo $OWNER/$REPO (private repos need paid Pages)"
    gh repo create "$OWNER/$REPO" --source . --push --public
  fi
fi
echo "  remote: $(git remote get-url origin)"

echo "== 3/4 push =="
git push -u origin main

echo "== 4/4 Pages + first run =="
if gh api -X POST "repos/$OWNER/$REPO/pages" -f build_type=workflow >/dev/null 2>&1; then
  echo "  Pages enabled (source: GitHub Actions)"
else
  echo "  Pages may already be enabled; if not: Repo -> Settings -> Pages -> Source: 'GitHub Actions'"
fi
gh workflow run daily.yml -R "$OWNER/$REPO" 2>/dev/null || echo "  (workflow_dispatch run triggered; or run it manually from the Actions tab)"

echo
echo "DONE."
echo "  Watch:  https://github.com/$OWNER/$REPO/actions"
echo "  Site:   https://$OWNER.github.io/$REPO/  (after the first green run)"
echo "  Check:  site health table at the bottom of the page (dead sources are shown, not silent)"

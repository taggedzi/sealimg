#!/usr/bin/env bash
set -euo pipefail

# Bootstrap GitHub labels, milestones, and initial epic issues for Sealimg.
# Requirements:
#   - gh CLI installed and authenticated
#   - run from repo root
#
# Usage:
#   scripts/bootstrap_github_project.sh
#   scripts/bootstrap_github_project.sh OWNER/REPO

if ! command -v gh >/dev/null 2>&1; then
  echo "Error: GitHub CLI (gh) is not installed."
  echo "Install gh, run 'gh auth login', then re-run this script."
  exit 1
fi

REPO="${1:-}"
if [[ -z "${REPO}" ]]; then
  REPO="$(gh repo view --json nameWithOwner -q .nameWithOwner)"
fi

echo "Bootstrapping GitHub project metadata for ${REPO}"

create_label() {
  local name="$1"
  local color="$2"
  local description="$3"

  if gh label list --repo "${REPO}" --limit 500 --search "${name}" --json name -q ".[].name" | grep -Fxq "${name}"; then
    echo "Label exists: ${name}"
  else
    gh label create "${name}" --repo "${REPO}" --color "${color}" --description "${description}"
    echo "Created label: ${name}"
  fi
}

create_milestone() {
  local title="$1"
  local description="$2"

  if gh api "repos/${REPO}/milestones" --paginate --jq '.[].title' | grep -Fxq "${title}"; then
    echo "Milestone exists: ${title}"
  else
    gh api "repos/${REPO}/milestones" --method POST -f title="${title}" -f description="${description}" >/dev/null
    echo "Created milestone: ${title}"
  fi
}

create_epic_issue() {
  local title="$1"
  local labels="$2"
  local milestone="$3"
  local body="$4"

  if gh issue list --repo "${REPO}" --search "in:title \"${title}\"" --state all --json title -q '.[].title' | grep -Fxq "${title}"; then
    echo "Issue exists: ${title}"
  else
    gh issue create --repo "${REPO}" --title "${title}" --label "${labels}" --milestone "${milestone}" --body "${body}" >/dev/null
    echo "Created issue: ${title}"
  fi
}

# Labels
create_label "epic" "5319E7" "Multi-issue initiative"
create_label "backend" "0052CC" "Core implementation and services"
create_label "cli" "1D76DB" "Command line behavior and UX"
create_label "crypto" "B60205" "Cryptography and key management"
create_label "metadata" "0E8A16" "IPTC/XMP/C2PA metadata handling"
create_label "c2pa" "0366D6" "C2PA/JUMBF embedding and provenance"
create_label "testing" "FBCA04" "Tests, fixtures, and QA"
create_label "docs" "0075CA" "Documentation changes"
create_label "security" "D93F0B" "Security and hardening"
create_label "platform" "C5DEF5" "Cross-platform behavior"
create_label "v0.1" "A2EEEF" "Roadmap v0.1 scope"
create_label "v0.3" "BFD4F2" "Roadmap v0.3 scope"
create_label "v0.5" "D4C5F9" "Roadmap v0.5 scope"
create_label "v0.7" "F9D0C4" "Roadmap v0.7 scope"
create_label "v1.0" "F9F2C4" "Roadmap v1.0 scope"

# Milestones
create_milestone "v0.1 MVP" "Initial CLI and provenance pipeline for PNG/JPEG."
create_milestone "v0.3 Embedding + Batch" "Best-effort C2PA embedding plus batch/watch workflow."
create_milestone "v0.5 Watermark + Timestamp" "Invisible watermark and public timestamp helper."
create_milestone "v0.7 Expanded Formats" "AVIF/HEIC/JPEG XL and advanced fingerprinting."
create_milestone "v1.0 GUI" "Local GUI and integration docs."

# Epics (from docs/github-issues-plan.md)
create_epic_issue \
  "epic: bootstrap python project and delivery pipeline" \
  "epic,backend,platform,v0.1" \
  "v0.1 MVP" \
  "Stand up Python project layout for library + CLI, CI baseline for Windows/Linux, and fixture conventions. See docs/github-issues-plan.md (Epic 1)."

create_epic_issue \
  "epic: implement config and manifest domain models" \
  "epic,backend,v0.1" \
  "v0.1 MVP" \
  "Implement config and manifest models, schema validation, image IDs, and profile precedence. See docs/github-issues-plan.md (Epic 2)."

create_epic_issue \
  "epic: key management and signing verification" \
  "epic,crypto,security,v0.1" \
  "v0.1 MVP" \
  "Implement keygen/sign/verify with native crypto plus optional GPG interop path. See docs/github-issues-plan.md (Epic 3)."

create_epic_issue \
  "epic: implement png/jpeg pipeline and metadata writing" \
  "epic,metadata,backend,v0.1" \
  "v0.1 MVP" \
  "Build PNG/JPEG processing, IPTC/XMP writing, pixel-preserving master, and web export. See docs/github-issues-plan.md (Epic 4)."

create_epic_issue \
  "epic: generate manifest hashes and provenance package outputs" \
  "epic,backend,cli,v0.1" \
  "v0.1 MVP" \
  "Generate hashes, manifest/signature outputs, README/ZIP packaging. See docs/github-issues-plan.md (Epic 5)."

create_epic_issue \
  "epic: implement sidecar-first c2pa embedding strategy" \
  "epic,c2pa,metadata,v0.3" \
  "v0.3 Embedding + Batch" \
  "Always emit sidecars; best-effort PNG/JPEG embedding with non-blocking fallback. See docs/github-issues-plan.md (Epic 6)."

create_epic_issue \
  "epic: implement cli commands and exit code contract" \
  "epic,cli,v0.1" \
  "v0.1 MVP" \
  "Implement command surface and deterministic exit code behavior. See docs/github-issues-plan.md (Epic 7)."

create_epic_issue \
  "epic: implement test plan and quality gates" \
  "epic,testing,security,platform,v0.1" \
  "v0.1 MVP" \
  "Implement functional/mutation/security/regression test coverage. See docs/github-issues-plan.md (Epic 8)."

create_epic_issue \
  "epic: finalize documentation for first release" \
  "epic,docs,v0.1" \
  "v0.1 MVP" \
  "Replace placeholders and align docs with implemented behavior. See docs/github-issues-plan.md (Epic 9)."

echo "Bootstrap complete."

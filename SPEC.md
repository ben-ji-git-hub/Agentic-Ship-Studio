# Product Spec

## Problem
AI-assisted builders can prototype quickly, but many projects lose trust at evaluation time due to missing quality and submission basics.

## Target User
Solo developers and small teams building with AI who need a fast, concrete path to ship credible projects.

## Success Metrics
- First audit runs in under 2 minutes.
- At least three actionable improvements surfaced on a typical prototype repo.
- Beginner can follow coach output and close one high-severity issue in under 15 minutes.

## Constraints
- Local-first, minimal setup.
- Deterministic and easy to run in CI.
- Safe defaults: auto-generated files must never overwrite existing files.

## Acceptance Criteria
- [x] CLI supports `init`, `audit`, `roadmap`, and `coach`.
- [x] `coach` output includes plain-English guidance and verification steps.
- [x] `--apply-safe` only creates missing baseline files.
- [x] Audit outputs JSON and Markdown reports.
- [x] Unit tests cover core paths.

## Non-Goals
- Replacing full enterprise security tooling.
- Auto-fixing business logic without developer review.

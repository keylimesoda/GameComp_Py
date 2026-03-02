# Repository Notes (Research Phase)

Last updated: 2026-03-02

## Current Status

- Project is in **research + iterative prototyping**.
- Core implementation exists under `src/gamecompanion/`.
- End-to-end scenario tests exist under `tests/e2e/` (M1-M6 milestone structure).
- Product and technical direction are still being validated and refined.

## Source of Truth Documents

- Product requirements: `spec.md`
- Test expectations: `test-spec.md`
- Research protocol: `research-protocol.md`
- Technical design sessions:
  - `tech-design-session.md`
  - `tech-review-notes.md`
  - `tech-review-v2-notes.md`
- Customer validation notes: `customer-validation-session.md`

## Project Layout (High-Level)

- `src/gamecompanion/` - application package + entry points
- `data/config.json` - runtime config used by the app
- `tests/e2e/` - end-to-end flow tests by milestone

## Immediate Next Steps

1. Stabilize M6 settings polish behavior in e2e.
2. Lock initial config schema and defaults.
3. Decide near-term branching/release strategy (`main` migration vs keep `master`).
4. Add CI for lint + tests on pull requests.

## Collaboration Notes

- Keep product/tech decisions documented in markdown first, then implement.
- Link PRs to relevant milestone tests and spec sections.
- Prefer small, milestone-scoped changes while requirements are still moving.
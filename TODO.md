# CoverAutomatic - TODO

## Session Notes (2026-01-03)

### Completed This Session
- Fixed persistence bug (debounced save mechanism for runtime changes)
- Fixed path traversal security vulnerability in import/export
- Fixed German umlauts in de.json
- Added Options Flow UI for cover configuration (facade, sensors, hysteresis)
- Made scenarios dynamic in services.yaml (no longer hardcoded)
- Added full UI for facade management (add/edit/delete)
- Added full UI for rule management with condition builder (11 condition types)
- Added full UI for scenario management (add/edit/delete/activate with icon selector)
- Created unit tests (81 tests: models, engine, storage)
- Set up GitHub Actions CI (tests on Python 3.11/3.12, HACS validation, Ruff linting)
- Fixed all Ruff linting warnings
- Switched to uv for virtual environment management
- Created project CLAUDE.md

### In Progress
- None

### Blockers / Open Questions
- None

### Next Steps
- Consider releasing v1.0.10 (remove -dev suffix) when ready for production
- Optional: Add integration tests with real Home Assistant mocks
- Optional: Add more edge case tests

---

## Open Tasks

- [ ] Release v1.0.10 stable (remove -dev, tag release)

## Completed (Archive)

- [x] Fix persistence bug (v1.0.6)
- [x] Fix path traversal vulnerability (v1.0.6)
- [x] Fix German umlauts (v1.0.6)
- [x] Add Options Flow UI for covers (v1.0.7)
- [x] Make scenarios dynamic (v1.0.8)
- [x] Add facade management UI (v1.0.9)
- [x] Add rule management UI (v1.0.9)
- [x] Add unit tests (v1.0.9)
- [x] Set up GitHub Actions CI (v1.0.9)
- [x] Add scenario management UI (v1.0.10)
- [x] Fix Ruff linting warnings (v1.0.10)

# FuelSight Documentation

This directory is the single public documentation set for FuelSight. It combines
the implemented product baseline, architecture, operating model, and future
roadmap without keeping separate AI-planning or phase-specific documentation trees.

## Start Here

- `project-idea.md` - product problem, solution, users, and MVP boundaries.
- `as-built-baseline.md` - current implemented capabilities and validation snapshot.
- `operability-and-defense-mode.md` - local demo, smoke, Airflow, and defense modes.
- `integrations-and-data-sources.md` - internal data, external indicators, news, and optional LLM/RAG strategy.
- `roadmap.md` - practical next improvements for the diploma and portfolio version.

## Detailed Specs

- `project/backend/` - backend architecture, API contracts, database, deployment, and ML pipeline.
- `project/frontend/` - frontend architecture, routes, state handling, and UI contracts.
- `features/` - feature-level behavior for auth, import, KPI, analytics, forecast, and news/chat.
- `screens/` - screen-level UI notes.
- `marketing/` - business context and positioning.

## Documentation Rules

- Runtime behavior and tests take precedence over stale prose.
- Keep `README.md` concise and update detailed docs here when contracts, demo flow, or supported degraded modes change.
- Do not store local secrets, generated reports, or AI-agent continuity notes in documentation.

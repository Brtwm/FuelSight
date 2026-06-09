from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _read_first(*paths: str) -> str:
    for path in paths:
        candidate = ROOT / path
        if candidate.exists():
            return candidate.read_text(encoding="utf-8")
    raise FileNotFoundError(paths[0])


def test_docs_do_not_reintroduce_stale_status_claims() -> None:
    docs = "\n".join(
        [
            _read("README.md"),
            _read_first("AGENTS.md", "AGENT.md", "DEVELOPMENT.md"),
            _read("docs/as-built-baseline.md"),
            _read("docs/project/backend/backend-docs.md"),
            _read("docs/project/backend/deployment.md"),
            _read("docs/roadmap.md"),
        ]
    ).lower()

    forbidden_claims = [
        "defense mode and executive outputs | docs_only",
        "chat generation возвращает controlled `503 llm_disabled`",
        "cloud calls остаются phase i",
        "cloud provider adapters remain phase i",
        "work" + "tree " + "сейчас грязный",
        "implemented + " + "work" + "tree",
    ]

    for claim in forbidden_claims:
        assert claim not in docs


def test_docs_define_public_documentation_sync_rule() -> None:
    docs = "\n".join(
        [
            _read("docs/README.md"),
            _read("docs/project/backend/backend-docs.md"),
            _read("docs/project/backend/deployment.md"),
            _read("docs/project/frontend/frontend-docs.md"),
        ]
    ).lower()

    assert "documentation sync rule" in docs
    assert "docs/" in docs
    assert "readme.md" in docs
    assert "memory" + "-bank" not in docs
    assert "docs_" + "fuelsight" not in docs

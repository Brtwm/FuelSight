from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_phase_k_docs_do_not_reintroduce_stale_phase_j_or_chat_claims() -> None:
    docs = "\n".join(
        [
            _read("docs_fuelsight/as-built-baseline.md"),
            _read("docs_fuelsight/project/backend/backend-docs.md"),
            _read("docs_fuelsight_2/phase0-gap-matrix.md"),
            _read("memory-bank/activeContext.md"),
            _read("memory-bank/progress.md"),
            _read("memory-bank/techContext.md"),
        ]
    ).lower()

    forbidden_claims = [
        "defense mode and executive outputs | docs_only",
        "chat generation возвращает controlled `503 llm_disabled`",
        "cloud calls остаются phase i",
        "cloud provider adapters remain phase i",
        "worktree сейчас грязный",
    ]

    for claim in forbidden_claims:
        assert claim not in docs


def test_phase_k_docs_define_mandatory_sync_rule() -> None:
    docs = "\n".join(
        [
            _read("docs_fuelsight/as-built-baseline.md"),
            _read("docs_fuelsight_2/phase0-gap-matrix.md"),
            _read("memory-bank/systemPatterns.md"),
        ]
    )

    assert "mandatory sync rule" in docs.lower()
    assert "memory-bank" in docs
    assert "docs_fuelsight" in docs
    assert "phase0-gap-matrix.md" in docs


def test_phase_k_docs_do_not_claim_worktree_only_when_git_tree_is_clean() -> None:
    status = subprocess.run(
        ["git", "status", "--short"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    assert status.returncode == 0
    if status.stdout.strip():
        return

    docs = "\n".join(
        [
            _read("docs_fuelsight/as-built-baseline.md"),
            _read("docs_fuelsight_2/phase0-gap-matrix.md"),
        ]
    )

    assert "implemented + worktree" not in docs

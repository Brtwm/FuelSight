from __future__ import annotations

from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _collect_doc_items(base: Path) -> set[str]:
    items: set[str] = set()
    for group in ("features", "screens"):
        for path in sorted((base / group).glob("*.md")):
            items.add(f"{group}/{path.name}")
    return items


def test_public_docs_cover_all_feature_and_screen_specs() -> None:
    root = _repo_root()
    docs_base = root / "docs"

    assert docs_base.exists(), "docs/ is the canonical public documentation directory"
    assert (docs_base / "README.md").exists(), "docs/README.md must explain the docs structure"
    assert (docs_base / "as-built-baseline.md").exists()
    assert (docs_base / "roadmap.md").exists()

    doc_items = _collect_doc_items(docs_base)
    expected_items = {
        "features/auth.md",
        "features/data-import.md",
        "features/demand-forecast.md",
        "features/kpi-dashboard.md",
        "features/news-digest-chat.md",
        "features/procurement-margin.md",
        "features/sales-analytics.md",
        "screens/screen-data-import.md",
        "screens/screen-demand-forecast.md",
        "screens/screen-kpi-dashboard.md",
        "screens/screen-login.md",
        "screens/screen-news-digest-chat.md",
        "screens/screen-procurement-margin.md",
        "screens/screen-sales-analytics.md",
    }

    assert expected_items.issubset(doc_items)


def test_public_docs_do_not_reference_removed_internal_doc_trees() -> None:
    root = _repo_root()
    public_docs = "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted((root / "docs").rglob("*.md"))
    ).lower()

    forbidden_terms = [
        "docs_" + "fuelsight",
        "docs_" + "fuelsight_2",
        "memory" + "-bank",
        "agents.md",
        "current " + "work" + "tree",
        "текущем " + "work" + "tree",
        "work" + "tree " + "сейчас",
        "co" + "dex/" + "fuelsight",
    ]

    for term in forbidden_terms:
        assert term not in public_docs

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


def _parse_markdown_table_rows(content: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line.startswith("|") or not line.endswith("|"):
            continue
        cells = [cell.strip() for cell in line.split("|")[1:-1]]
        if len(cells) != 7:
            continue
        if cells[0] in {"doc_item", "---"}:
            continue
        rows.append(
            {
                "doc_item": cells[0],
                "scope_or_route": cells[1],
                "current_module": cells[2],
                "target_module": cells[3],
                "test_target": cells[4],
                "gap_type": cells[5],
                "next_slice": cells[6],
            }
        )
    return rows


def test_phase0_gap_matrix_covers_all_v2_feature_and_screen_docs() -> None:
    root = _repo_root()
    docs_base = root / "docs_fuelsight_2"
    matrix_path = docs_base / "phase0-gap-matrix.md"

    assert matrix_path.exists(), "phase0-gap-matrix.md is required for phase 0 contracts freeze"

    rows = _parse_markdown_table_rows(matrix_path.read_text(encoding="utf-8"))
    assert rows, "phase0-gap-matrix.md must contain data rows"

    matrix_doc_items = {row["doc_item"] for row in rows}
    actual_doc_items = _collect_doc_items(docs_base)
    assert actual_doc_items.issubset(matrix_doc_items)
    assert len(rows) == len(matrix_doc_items), "doc_item entries must be unique in matrix"

    allowed_statuses = {
        "implemented",
        "implemented_mvp",
        "implemented + worktree",
        "partial",
        "docs_only",
    }

    for row in rows:
        doc_path = docs_base / row["doc_item"]
        assert doc_path.exists(), f"Missing doc for matrix row: {row['doc_item']}"
        assert row["current_module"] in allowed_statuses, (
            f"Unexpected status marker '{row['current_module']}' for {row['doc_item']}"
        )
        assert row["test_target"], f"Missing test_target for {row['doc_item']}"
        assert row["next_slice"], f"Missing next_slice for {row['doc_item']}"

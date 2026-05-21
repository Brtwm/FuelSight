from __future__ import annotations

from app.api.v1.router import api_router


def _extract_top_level_groups() -> set[str]:
    groups: set[str] = set()
    for route in api_router.routes:
        path = getattr(route, "path", "")
        if not path.startswith("/api/v1/"):
            continue
        tail = path.removeprefix("/api/v1/")
        segment = tail.split("/", maxsplit=1)[0].strip()
        if segment:
            groups.add(segment)
    return groups


def test_top_level_api_groups_remain_stable() -> None:
    groups = _extract_top_level_groups()
    expected = {
        "auth",
        "health",
        "import",
        "kpi",
        "analytics",
        "forecasts",
        "backtests",
        "news",
        "chat",
        "reports",
    }
    assert groups == expected

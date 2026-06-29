from __future__ import annotations

from collections.abc import Iterator
from typing import Any


def iter_route_paths(router: Any, prefix: str = "") -> Iterator[str]:
    for route in router.routes:
        path = getattr(route, "path", None)
        if path is not None:
            yield f"{prefix}{path}"
            continue

        included_router = getattr(route, "original_router", None)
        include_context = getattr(route, "include_context", None)
        if included_router is not None and include_context is not None:
            yield from iter_route_paths(
                included_router,
                prefix=f"{prefix}{include_context.prefix}",
            )

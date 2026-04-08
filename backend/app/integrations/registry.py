from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any


IntegrationFactory = Callable[[], Any]


@dataclass
class IntegrationRegistry:
    _items: dict[str, IntegrationFactory] = field(default_factory=dict)

    def register(self, key: str, factory: IntegrationFactory) -> None:
        normalized = key.strip().lower()
        if not normalized:
            raise ValueError("integration key is required")
        self._items[normalized] = factory

    def resolve(self, key: str) -> Any:
        normalized = key.strip().lower()
        if normalized not in self._items:
            raise KeyError(f"integration '{key}' is not registered")
        return self._items[normalized]()

    def keys(self) -> list[str]:
        return sorted(self._items.keys())


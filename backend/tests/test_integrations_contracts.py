from __future__ import annotations

from app.integrations.mode_resolver import resolve_integration_mode
from app.integrations.registry import IntegrationRegistry


def test_integration_mode_resolver_prefers_live_then_cache_then_manual() -> None:
    assert (
        resolve_integration_mode(
            prefer_live=True,
            live_available=True,
            cache_available=True,
        ).mode
        == "live"
    )
    assert (
        resolve_integration_mode(
            prefer_live=True,
            live_available=False,
            cache_available=True,
        ).mode
        == "cached"
    )
    assert (
        resolve_integration_mode(
            prefer_live=False,
            live_available=False,
            cache_available=False,
        ).mode
        == "manual_snapshot"
    )


def test_integration_registry_register_and_resolve() -> None:
    registry = IntegrationRegistry()
    registry.register("news", lambda: {"provider": "news"})
    assert registry.keys() == ["news"]
    assert registry.resolve("news") == {"provider": "news"}

from __future__ import annotations

from typing import Protocol

from app.integrations.contracts import IntegrationResult


class NewsIngestAdapter(Protocol):
    provider_name: str

    def fetch_latest(self) -> IntegrationResult: ...


from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from app.integrations.contracts import IntegrationResult


class ExternalIndicatorsAdapter(Protocol):
    provider_name: str

    def fetch_daily(self, *, indicator_codes: Sequence[str]) -> IntegrationResult: ...


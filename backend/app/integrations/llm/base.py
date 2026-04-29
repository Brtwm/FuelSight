from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Protocol

from app.schemas.common import ProviderMode


class LlmAdapter(Protocol):
    provider_name: str
    mode: ProviderMode

    def generate(
        self,
        *,
        prompt: str,
        context_chunks: Sequence[str],
        evidence_pack: dict[str, Any] | None = None,
    ) -> str: ...

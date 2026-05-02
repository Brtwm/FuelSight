from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any, Protocol

from app.schemas.common import ProviderMode


@dataclass(frozen=True)
class LlmChatRequest:
    question: str
    evidence_pack: dict[str, Any]
    citations: list[dict[str, Any]]
    running_summary: str | None = None
    language: str = "ru"


@dataclass(frozen=True)
class LlmChatResult:
    answer: str
    provider: str
    mode: ProviderMode
    model: str | None = None
    usage: dict[str, Any] = field(default_factory=dict)
    degradation_reason: str | None = None


@dataclass(frozen=True)
class EmbeddingResult:
    vectors: list[list[float]]
    provider: str
    mode: ProviderMode
    model: str | None = None
    degradation_reason: str | None = None


@dataclass(frozen=True)
class RerankDocument:
    index: int
    text: str


@dataclass(frozen=True)
class RerankResult:
    scores: dict[int, float]
    provider: str
    mode: ProviderMode
    model: str | None = None
    degradation_reason: str | None = None


@dataclass(frozen=True)
class LlmHealth:
    provider: str
    mode: ProviderMode
    available: bool
    model: str | None = None
    degradation_reason: str | None = None


class LlmAdapter(Protocol):
    provider_name: str
    mode: ProviderMode
    chat_model: str | None

    def chat(self, request: LlmChatRequest) -> LlmChatResult: ...

    def embed_texts(self, texts: Sequence[str]) -> EmbeddingResult: ...

    def rerank(self, *, query: str, documents: Sequence[RerankDocument]) -> RerankResult: ...

    def health(self) -> LlmHealth: ...

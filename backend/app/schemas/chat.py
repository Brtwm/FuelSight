from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from app.schemas.common import ProviderMode

ChatContextScope = Literal[
    "internal_analytics",
    "news_digest",
    "news_raw",
    "news_digests",
    "kpi",
    "analytics",
    "forecast",
]
ChatSenderType = Literal["user", "assistant"]
CitationType = Literal["news", "digest", "kpi", "chart", "forecast"]
ChatAnswerMode = Literal["cloud_llm", "local_llm", "retrieval_only"]


class CitationPayload(BaseModel):
    type: CitationType
    ref_id: str
    title: str
    provider_mode: ProviderMode
    confidence: float
    source_type: str
    url: str | None = None
    published_at: datetime | None = None
    route_path: str | None = None
    snippet: str | None = None


class ChatSessionCreateRequest(BaseModel):
    title: str = Field(min_length=3, max_length=255)

    @model_validator(mode="after")
    def _normalize(self) -> "ChatSessionCreateRequest":
        self.title = self.title.strip()
        return self


class ChatSessionPayload(BaseModel):
    id: UUID
    title: str
    created_at: datetime
    updated_at: datetime


class ChatMessagePayload(BaseModel):
    id: UUID
    sender_type: ChatSenderType
    message_text: str
    citations: list[CitationPayload] | None = None
    created_at: datetime


class ChatAskRequest(BaseModel):
    question: str = Field(min_length=3)
    context_scope: list[ChatContextScope] = Field(
        default_factory=lambda: ["internal_analytics", "news_digest"]
    )

    @model_validator(mode="after")
    def _normalize(self) -> "ChatAskRequest":
        self.question = self.question.strip()
        return self


class ChatAnswerPayload(BaseModel):
    answer: str
    citations: list[CitationPayload]
    mode: ChatAnswerMode
    provider_mode: ProviderMode

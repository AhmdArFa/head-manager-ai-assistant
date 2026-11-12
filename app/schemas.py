from typing import Any, Literal

from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    question: str = Field(min_length=2, max_length=1000, description="Company question")


class SourceEvidence(BaseModel):
    table: str
    query_id: str
    row_count: int


class TraceStep(BaseModel):
    step: str
    component: str
    status: Literal["completed", "skipped"]
    detail: str


class AskResponse(BaseModel):
    request_id: str
    question: str
    intent: str
    answer: str
    data: list[dict[str, Any]] = Field(default_factory=list)
    sources: list[SourceEvidence] = Field(default_factory=list)
    trace: list[TraceStep] = Field(default_factory=list)


class HealthResponse(BaseModel):
    status: Literal["ok"]
    service: str

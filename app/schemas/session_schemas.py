from datetime import datetime
from typing import Any

from pydantic import BaseModel


class SessionCreate(BaseModel):
    customer_name: str | None = None
    customer_email: str | None = None
    room: str | None = None


class SessionResponse(BaseModel):
    id: int
    customer_name: str | None = None
    customer_email: str | None = None
    room: str | None = None
    status: str
    started_at: datetime
    updated_at: datetime | None = None
    supervisor_id: int | None = None
    supervisor_name: str | None = None


class AssignSupervisorRequest(BaseModel):
    supervisor_id: int


class AnswerEntry(BaseModel):
    question_key: str
    answer_value: Any


class SingleAnswerUpdate(BaseModel):
    question_key: str
    answer_value: Any


class SessionAnswersUpdate(BaseModel):
    answers: list[AnswerEntry]


class SessionDetailResponse(BaseModel):
    session: SessionResponse
    answers: list[AnswerEntry]

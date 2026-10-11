from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

Identifier = Annotated[
    str, StringConstraints(min_length=1, max_length=64, pattern=r"^[a-zA-Z0-9][a-zA-Z0-9_-]*$")
]


class Record(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class Tenant(Record):
    id: Identifier
    name: str


class Learner(Record):
    id: Identifier
    tenant_id: Identifier


class Course(Record):
    id: Identifier
    tenant_id: Identifier
    title: str


class Content(Record):
    id: Identifier
    tenant_id: Identifier
    course_id: Identifier
    title: str
    body: str
    approved: bool


class Progress(Record):
    learner_id: Identifier
    tenant_id: Identifier
    course_id: Identifier
    completion_percent: Annotated[float, Field(ge=0, le=100)]


class Principal(Record):
    subject: Identifier
    tenant_id: Identifier
    type: Literal["human"] = "human"


class PublicContent(Record):
    id: Identifier
    course_id: Identifier
    title: str
    body: str


class ContentCollection(Record):
    items: list[PublicContent]


class PublicProgress(Record):
    learner_id: Identifier
    course_id: Identifier
    completion_percent: Annotated[float, Field(ge=0, le=100)]


class Health(Record):
    status: Literal["ok"] = "ok"
    version: str

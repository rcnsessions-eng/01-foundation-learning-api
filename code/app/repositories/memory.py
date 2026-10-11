from typing import Protocol

from app.domain import Content, Course, Learner, Principal, Progress, Tenant


class LearningRepository(Protocol):
    def list_approved_content(self, tenant_id: str, limit: int) -> tuple[Content, ...]: ...

    def get_progress(self, tenant_id: str, learner_id: str) -> Progress | None: ...


class InMemoryLearningRepository:
    def __init__(self) -> None:
        self.tenants = (
            Tenant(id="tenant-red", name="Synthetic Red Academy"),
            Tenant(id="tenant-blue", name="Synthetic Blue Academy"),
        )
        self.learners = (
            Learner(id="learner-red-1", tenant_id="tenant-red"),
            Learner(id="learner-red-2", tenant_id="tenant-red"),
            Learner(id="learner-blue-1", tenant_id="tenant-blue"),
        )
        self.courses = (
            Course(id="course-red", tenant_id="tenant-red", title="Synthetic routing basics"),
            Course(
                id="course-blue", tenant_id="tenant-blue", title="Synthetic security basics"
            ),
        )
        self.content = (
            Content(
                id="content-red-approved",
                tenant_id="tenant-red",
                course_id="course-red",
                title="Synthetic routing basics",
                body="A router connects synthetic networks.",
                approved=True,
            ),
            Content(
                id="content-red-draft",
                tenant_id="tenant-red",
                course_id="course-red",
                title="Unapproved draft",
                body="Unreleased synthetic text.",
                approved=False,
            ),
            Content(
                id="content-blue-approved",
                tenant_id="tenant-blue",
                course_id="course-blue",
                title="Synthetic security basics",
                body="A policy constrains a synthetic action.",
                approved=True,
            ),
        )
        self.progress = tuple(
            Progress(
                learner_id=learner.id,
                tenant_id=learner.tenant_id,
                course_id="course-red" if learner.tenant_id == "tenant-red" else "course-blue",
                completion_percent=25.0 * (index + 1),
            )
            for index, learner in enumerate(self.learners)
        )

    def list_approved_content(self, tenant_id: str, limit: int) -> tuple[Content, ...]:
        return tuple(
            content
            for content in self.content
            if content.tenant_id == tenant_id and content.approved
        )[:limit]

    def get_progress(self, tenant_id: str, learner_id: str) -> Progress | None:
        return next(
            (
                record
                for record in self.progress
                if record.tenant_id == tenant_id and record.learner_id == learner_id
            ),
            None,
        )


def demo_principals() -> dict[str, Principal]:
    return {
        "learner-red-1": Principal(subject="learner-red-1", tenant_id="tenant-red"),
        "learner-red-2": Principal(subject="learner-red-2", tenant_id="tenant-red"),
        "learner-blue-1": Principal(subject="learner-blue-1", tenant_id="tenant-blue"),
    }

from app.domain import ContentCollection, Principal, PublicContent, PublicProgress
from app.errors import ServiceError
from app.repositories.memory import LearningRepository


class LearningService:
    def __init__(self, repository: LearningRepository) -> None:
        self.repository = repository

    def list_content(self, principal: Principal, limit: int) -> ContentCollection:
        records = self.repository.list_approved_content(principal.tenant_id, limit)
        return ContentCollection(
            items=[
                PublicContent(
                    id=record.id,
                    course_id=record.course_id,
                    title=record.title,
                    body=record.body,
                )
                for record in records
            ]
        )

    def read_progress(self, principal: Principal, learner_id: str) -> PublicProgress:
        if principal.subject != learner_id:
            raise ServiceError(404, "not_found", "Resource not found")
        record = self.repository.get_progress(principal.tenant_id, learner_id)
        if record is None:
            raise ServiceError(404, "not_found", "Resource not found")
        return PublicProgress(
            learner_id=record.learner_id,
            course_id=record.course_id,
            completion_percent=record.completion_percent,
        )

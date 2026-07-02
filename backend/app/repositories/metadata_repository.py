from sqlalchemy.orm import Session

from app.models.project_metadata import ProjectMetadata


class MetadataRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_project_id(self, project_id: int) -> ProjectMetadata | None:
        return (
            self.db.query(ProjectMetadata)
            .filter(ProjectMetadata.project_id == project_id)
            .first()
        )

    def upsert(self, project_id: int, data: dict) -> ProjectMetadata:
        existing = self.get_by_project_id(project_id)
        if existing:
            for key, value in data.items():
                setattr(existing, key, value)
            self.db.commit()
            self.db.refresh(existing)
            return existing

        metadata = ProjectMetadata(project_id=project_id, **data)
        self.db.add(metadata)
        self.db.commit()
        self.db.refresh(metadata)
        return metadata

    def delete_by_project_id(self, project_id: int) -> None:
        metadata = self.get_by_project_id(project_id)
        if metadata:
            self.db.delete(metadata)
            self.db.commit()

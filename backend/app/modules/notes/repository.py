"""Repositorios de Notas, etiquetas y vínculos."""

from __future__ import annotations

import re

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.modules.notes.models import Note, NoteProjectLink, NoteTag, NoteTaskLink, Tag
from app.modules.notes.schemas import NoteCreate, NoteUpdate, TagCreate


def normalize_tag_name(name: str) -> str:
    """Normaliza nombre de etiqueta: quita espacios externos, colapsa repetidos, casefold."""
    collapsed = re.sub(r"\s+", " ", name.strip())
    return collapsed.casefold()


class NoteRepository:
    """Acceso a datos de la entidad Note."""

    def __init__(self, db: Session):
        self.db = db

    def get(self, note_id: str) -> Note | None:
        return self.db.get(Note, note_id)

    def get_with_links(self, note_id: str) -> Note | None:
        stmt = (
            select(Note)
            .where(Note.id == note_id)
            .options(
                selectinload(Note.project_links),
                selectinload(Note.task_links),
                selectinload(Note.tag_links).joinedload(NoteTag.tag),
            )
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def list(
        self,
        search: str | None = None,
        tag_id: str | None = None,
        project_id: str | None = None,
        task_id: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Note]:
        stmt = select(Note)
        conditions = []
        if search:
            like = f"%{search}%"
            conditions.append(
                or_(Note.title.ilike(like), Note.content.ilike(like))
            )
        if tag_id is not None:
            stmt = stmt.join(NoteTag).where(NoteTag.tag_id == tag_id)
        if project_id is not None:
            # Consultar las notas de un proyecto (FR-NOTE-07: vínculos desde
            # ambos lados)
            stmt = stmt.join(NoteProjectLink).where(
                NoteProjectLink.project_id == project_id
            )
        if task_id is not None:
            stmt = stmt.join(NoteTaskLink).where(
                NoteTaskLink.task_id == task_id
            )
        if conditions:
            stmt = stmt.where(and_(*conditions))
        stmt = stmt.order_by(Note.updated_at.desc()).offset(skip).limit(limit)
        return list(self.db.execute(stmt).scalars().all())

    def count(self) -> int:
        return self.db.execute(select(func.count(Note.id))).scalar_one()

    def create(self, note_in: NoteCreate) -> Note:
        db_obj = Note(title=note_in.title, content=note_in.content)
        self.db.add(db_obj)
        self.db.flush()
        self.db.refresh(db_obj)
        return db_obj

    def update(self, db_obj: Note, note_in: NoteUpdate) -> Note:
        data = note_in.model_dump(exclude_unset=True)
        for field, value in data.items():
            setattr(db_obj, field, value)
        from app.core.utils import utc_now

        db_obj.updated_at = utc_now()
        self.db.add(db_obj)
        self.db.flush()
        self.db.refresh(db_obj)
        return db_obj

    def delete(self, db_obj: Note) -> None:
        self.db.delete(db_obj)
        self.db.flush()


class TagRepository:
    """Acceso a datos de la entidad Tag."""

    def __init__(self, db: Session):
        self.db = db

    def get(self, tag_id: str) -> Tag | None:
        return self.db.get(Tag, tag_id)

    def get_by_normalized(self, normalized_name: str) -> Tag | None:
        stmt = select(Tag).where(Tag.normalized_name == normalized_name)
        return self.db.execute(stmt).scalar_one_or_none()

    def list(self, skip: int = 0, limit: int = 100) -> list[Tag]:
        stmt = select(Tag).order_by(Tag.name).offset(skip).limit(limit)
        return list(self.db.execute(stmt).scalars().all())

    def create(self, tag_in: TagCreate) -> Tag:
        normalized = normalize_tag_name(tag_in.name)
        existing = self.get_by_normalized(normalized)
        if existing is not None:
            # Devolver la existente para permitir reutilización sin duplicar
            return existing
        db_obj = Tag(name=tag_in.name.strip(), normalized_name=normalized)
        self.db.add(db_obj)
        self.db.flush()
        self.db.refresh(db_obj)
        return db_obj

    def delete(self, db_obj: Tag) -> None:
        self.db.delete(db_obj)
        self.db.flush()


class NoteLinkRepository:
    """Operaciones de vínculos nota-proyecto, nota-tarea y nota-etiqueta."""

    def __init__(self, db: Session):
        self.db = db

    # --- proyecto ---
    def link_project(self, note_id: str, project_id: str) -> None:
        existing = self.db.execute(
            select(NoteProjectLink).where(
                and_(
                    NoteProjectLink.note_id == note_id,
                    NoteProjectLink.project_id == project_id,
                )
            )
        ).scalar_one_or_none()
        if existing is None:
            link = NoteProjectLink(note_id=note_id, project_id=project_id)
            self.db.add(link)
            self.db.flush()

    def unlink_project(self, note_id: str, project_id: str) -> bool:
        link = self.db.execute(
            select(NoteProjectLink).where(
                and_(
                    NoteProjectLink.note_id == note_id,
                    NoteProjectLink.project_id == project_id,
                )
            )
        ).scalar_one_or_none()
        if link is None:
            return False
        self.db.delete(link)
        self.db.flush()
        return True

    def get_projects_for_note(self, note_id: str):
        from app.modules.projects.models import Project

        stmt = (
            select(Project)
            .join(NoteProjectLink)
            .where(NoteProjectLink.note_id == note_id)
        )
        return list(self.db.execute(stmt).scalars().all())

    # --- tarea ---
    def link_task(self, note_id: str, task_id: str) -> None:
        existing = self.db.execute(
            select(NoteTaskLink).where(
                and_(
                    NoteTaskLink.note_id == note_id,
                    NoteTaskLink.task_id == task_id,
                )
            )
        ).scalar_one_or_none()
        if existing is None:
            link = NoteTaskLink(note_id=note_id, task_id=task_id)
            self.db.add(link)
            self.db.flush()

    def unlink_task(self, note_id: str, task_id: str) -> bool:
        link = self.db.execute(
            select(NoteTaskLink).where(
                and_(
                    NoteTaskLink.note_id == note_id,
                    NoteTaskLink.task_id == task_id,
                )
            )
        ).scalar_one_or_none()
        if link is None:
            return False
        self.db.delete(link)
        self.db.flush()
        return True

    def get_tasks_for_note(self, note_id: str):
        from app.modules.tasks.models import Task

        stmt = (
            select(Task)
            .join(NoteTaskLink)
            .where(NoteTaskLink.note_id == note_id)
        )
        return list(self.db.execute(stmt).scalars().all())

    # --- etiqueta ---
    def link_tag(self, note_id: str, tag_id: str) -> None:
        existing = self.db.execute(
            select(NoteTag).where(
                and_(
                    NoteTag.note_id == note_id,
                    NoteTag.tag_id == tag_id,
                )
            )
        ).scalar_one_or_none()
        if existing is None:
            link = NoteTag(note_id=note_id, tag_id=tag_id)
            self.db.add(link)
            self.db.flush()

    def unlink_tag(self, note_id: str, tag_id: str) -> bool:
        link = self.db.execute(
            select(NoteTag).where(
                and_(
                    NoteTag.note_id == note_id,
                    NoteTag.tag_id == tag_id,
                )
            )
        ).scalar_one_or_none()
        if link is None:
            return False
        self.db.delete(link)
        self.db.flush()
        return True

    def get_tags_for_note(self, note_id: str):
        stmt = (
            select(Tag)
            .join(NoteTag)
            .where(NoteTag.note_id == note_id)
            .order_by(Tag.name)
        )
        return list(self.db.execute(stmt).scalars().all())

    def get_notes_for_tag(self, tag_id: str):
        stmt = (
            select(Note)
            .join(NoteTag)
            .where(NoteTag.tag_id == tag_id)
            .order_by(Note.updated_at.desc())
        )
        return list(self.db.execute(stmt).scalars().all())
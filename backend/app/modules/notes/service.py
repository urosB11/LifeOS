"""Servicio de Notas, vínculos y etiquetas.

Implementa reglas de negocio y registra eventos de actividad en la misma
transacción que el cambio de dominio (DATABASE.md sección 6).
"""

from __future__ import annotations

from app.db.activity import record_event
from app.modules.notes.models import Note, Tag
from app.modules.notes.repository import (
    NoteLinkRepository,
    NoteRepository,
    TagRepository,
)
from app.modules.notes.schemas import NoteCreate, NoteUpdate, TagCreate
from app.modules.projects.repository import ProjectRepository
from app.modules.tasks.repository import TaskRepository


class NoteService:
    """Casos de uso de notas."""

    def __init__(
        self,
        note_repo: NoteRepository,
        link_repo: NoteLinkRepository,
        tag_repo: TagRepository,
        project_repo: ProjectRepository,
        task_repo: TaskRepository,
        db,
    ):
        self.note_repo = note_repo
        self.link_repo = link_repo
        self.tag_repo = tag_repo
        self.project_repo = project_repo
        self.task_repo = task_repo
        self.db = db

    def create(self, note_in: NoteCreate) -> Note:
        note = self.note_repo.create(note_in)
        record_event(
            self.db,
            event_type="note.created",
            entity_type="note",
            entity_id=note.id,
            metadata={"title": note.title},
        )
        return note

    def get(self, note_id: str) -> Note | None:
        return self.note_repo.get_with_links(note_id)

    def list(
        self,
        search: str | None = None,
        tag_id: str | None = None,
    ):
        return self.note_repo.list(search=search, tag_id=tag_id)

    def update(self, note_id: str, note_in: NoteUpdate) -> Note | None:
        note = self.note_repo.get(note_id)
        if note is None:
            return None
        updated = self.note_repo.update(note, note_in)
        record_event(
            self.db,
            event_type="note.updated",
            entity_type="note",
            entity_id=note_id,
            metadata={"fields": list(note_in.model_dump(exclude_unset=True).keys())},
        )
        return updated

    def delete(self, note_id: str) -> bool:
        note = self.note_repo.get(note_id)
        if note is None:
            return False
        self.note_repo.delete(note)
        record_event(
            self.db,
            event_type="note.deleted",
            entity_type="note",
            entity_id=note_id,
        )
        return True

    # --- vínculos proyecto ---
    def link_project(self, note_id: str, project_id: str) -> bool:
        note = self.note_repo.get(note_id)
        if note is None:
            return False
        project = self.project_repo.get(project_id)
        if project is None:
            return False
        self.link_repo.link_project(note_id, project_id)
        self._touch_note(note_id)
        record_event(
            self.db,
            event_type="note.updated",
            entity_type="note",
            entity_id=note_id,
            metadata={"change": "project_link_added", "linked_id": project_id},
        )
        return True

    def unlink_project(self, note_id: str, project_id: str) -> bool:
        note = self.note_repo.get(note_id)
        if note is None:
            return False
        ok = self.link_repo.unlink_project(note_id, project_id)
        if ok:
            self._touch_note(note_id)
            record_event(
                self.db,
                event_type="note.updated",
                entity_type="note",
                entity_id=note_id,
                metadata={"change": "project_link_removed", "linked_id": project_id},
            )
        return ok

    def get_projects(self, note_id: str):
        return self.link_repo.get_projects_for_note(note_id)

    # --- vínculos tarea ---
    def link_task(self, note_id: str, task_id: str) -> bool:
        note = self.note_repo.get(note_id)
        if note is None:
            return False
        task = self.task_repo.get(task_id)
        if task is None:
            return False
        self.link_repo.link_task(note_id, task_id)
        self._touch_note(note_id)
        record_event(
            self.db,
            event_type="note.updated",
            entity_type="note",
            entity_id=note_id,
            metadata={"change": "task_link_added", "linked_id": task_id},
        )
        return True

    def unlink_task(self, note_id: str, task_id: str) -> bool:
        note = self.note_repo.get(note_id)
        if note is None:
            return False
        ok = self.link_repo.unlink_task(note_id, task_id)
        if ok:
            self._touch_note(note_id)
            record_event(
                self.db,
                event_type="note.updated",
                entity_type="note",
                entity_id=note_id,
                metadata={"change": "task_link_removed", "linked_id": task_id},
            )
        return ok

    def get_tasks(self, note_id: str):
        return self.link_repo.get_tasks_for_note(note_id)

    # --- etiquetas ---
    def link_tag(self, note_id: str, tag_id: str) -> bool:
        note = self.note_repo.get(note_id)
        tag = self.tag_repo.get(tag_id)
        if note is None or tag is None:
            return False
        self.link_repo.link_tag(note_id, tag_id)
        self._touch_note(note_id)
        record_event(
            self.db,
            event_type="note.updated",
            entity_type="note",
            entity_id=note_id,
            metadata={"change": "tag_added", "linked_id": tag_id},
        )
        return True

    def unlink_tag(self, note_id: str, tag_id: str) -> bool:
        note = self.note_repo.get(note_id)
        if note is None:
            return False
        ok = self.link_repo.unlink_tag(note_id, tag_id)
        if ok:
            self._touch_note(note_id)
            record_event(
                self.db,
                event_type="note.updated",
                entity_type="note",
                entity_id=note_id,
                metadata={"change": "tag_removed", "linked_id": tag_id},
            )
        return ok

    def get_tags(self, note_id: str):
        return self.link_repo.get_tags_for_note(note_id)

    def get_notes_for_tag(self, tag_id: str):
        return self.link_repo.get_notes_for_tag(tag_id)

    def _touch_note(self, note_id: str) -> None:
        note = self.note_repo.get(note_id)
        if note:
            from app.core.utils import utc_now

            note.updated_at = utc_now()
            self.db.add(note)
            self.db.flush()


class TagService:
    """Casos de uso de etiquetas."""

    def __init__(self, tag_repo: TagRepository, db):
        self.tag_repo = tag_repo
        self.db = db

    def create(self, tag_in: TagCreate) -> Tag:
        tag = self.tag_repo.create(tag_in)
        record_event(
            self.db,
            event_type="tag.created",
            entity_type="tag",
            entity_id=tag.id,
            metadata={"name": tag.name},
        )
        return tag

    def list(self):
        return self.tag_repo.list()

    def get(self, tag_id: str) -> Tag | None:
        return self.tag_repo.get(tag_id)
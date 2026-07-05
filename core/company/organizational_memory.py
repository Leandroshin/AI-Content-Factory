"""Organizational Memory Runtime — permanent institutional memory.

This is NOT employee memory. It is company-wide persistent knowledge:
brand guidelines, templates, best practices, approved decisions,
lessons learned, internal rules, quality standards, known assets,
and procedures. Every query is deterministic.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from core.events.bus import EventBus
from core.events.domain_events import (
    MemoryDocumentArchived,
    MemoryDocumentCreated,
    MemoryDocumentUpdated,
)


@dataclass(frozen=True, slots=True)
class OrganizationalDocument:
    id: UUID
    title: str
    category: str
    tags: tuple[str, ...]
    created_at: float
    updated_at: float
    version: int
    status: str  # "active" | "archived"
    author: str
    content: str
    source: str


class OrganizationalMemoryRuntime:
    """Permanent institutional memory for the AI Company.

    Documents are immutable — updates produce a new version.
    All search operations are deterministic O(n) on active documents.

    Usage::

        mem = OrganizationalMemoryRuntime(event_bus=bus)
        doc = mem.register_document("Brand Voice", "guidelines",
                                     "Use casual Portuguese...", "CEO")
        found = mem.search("Brand", category="guidelines")
    """

    def __init__(self, event_bus: EventBus | None = None) -> None:
        self._documents: dict[UUID, OrganizationalDocument] = {}
        self._event_bus = event_bus

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def register_document(
        self,
        title: str,
        category: str,
        content: str,
        author: str,
        source: str = "",
        tags: tuple[str, ...] | None = None,
    ) -> OrganizationalDocument:
        now = datetime.now().timestamp()
        doc = OrganizationalDocument(
            id=uuid4(),
            title=title,
            category=category,
            tags=tags or (),
            created_at=now,
            updated_at=now,
            version=1,
            status="active",
            author=author,
            content=content,
            source=source,
        )
        self._documents[doc.id] = doc
        self._publish(
            MemoryDocumentCreated(
                document_id=doc.id,
                title=doc.title,
                category=doc.category,
                timestamp=now,
                metadata={},
            )
        )
        return doc

    def update_document(
        self,
        doc_id: UUID,
        *,
        title: str | None = None,
        category: str | None = None,
        content: str | None = None,
        source: str | None = None,
        tags: tuple[str, ...] | None = None,
    ) -> OrganizationalDocument | None:
        doc = self._documents.get(doc_id)
        if doc is None:
            return None
        now = datetime.now().timestamp()
        new_doc = OrganizationalDocument(
            id=doc.id,
            title=title if title is not None else doc.title,
            category=category if category is not None else doc.category,
            tags=tags if tags is not None else doc.tags,
            created_at=doc.created_at,
            updated_at=now,
            version=doc.version + 1,
            status=doc.status,
            author=doc.author,
            content=content if content is not None else doc.content,
            source=source if source is not None else doc.source,
        )
        self._documents[doc_id] = new_doc
        self._publish(
            MemoryDocumentUpdated(
                document_id=new_doc.id,
                title=new_doc.title,
                category=new_doc.category,
                version=new_doc.version,
                timestamp=now,
                metadata={},
            )
        )
        return new_doc

    def archive_document(self, doc_id: UUID) -> OrganizationalDocument | None:
        doc = self._documents.get(doc_id)
        if doc is None or doc.status == "archived":
            return None
        now = datetime.now().timestamp()
        new_doc = OrganizationalDocument(
            id=doc.id,
            title=doc.title,
            category=doc.category,
            tags=doc.tags,
            created_at=doc.created_at,
            updated_at=now,
            version=doc.version,
            status="archived",
            author=doc.author,
            content=doc.content,
            source=doc.source,
        )
        self._documents[doc_id] = new_doc
        self._publish(
            MemoryDocumentArchived(
                document_id=new_doc.id,
                title=new_doc.title,
                timestamp=now,
                metadata={},
            )
        )
        return new_doc

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def get_document(self, doc_id: UUID) -> OrganizationalDocument | None:
        return self._documents.get(doc_id)

    def search(
        self,
        query: str,
        category: str | None = None,
        tags: tuple[str, ...] | None = None,
    ) -> tuple[OrganizationalDocument, ...]:
        q = query.lower()
        results: list[OrganizationalDocument] = []
        for doc in self._documents.values():
            if doc.status == "archived":
                continue
            if q and q not in doc.title.lower() and q not in doc.content.lower():
                continue
            if category is not None and doc.category != category:
                continue
            if tags is not None and not all(t in doc.tags for t in tags):
                continue
            results.append(doc)
        return tuple(results)

    def list_categories(self) -> tuple[str, ...]:
        return tuple(sorted({d.category for d in self._documents.values()}))

    def list_documents(
        self,
        category: str | None = None,
        status: str | None = "active",
    ) -> tuple[OrganizationalDocument, ...]:
        docs = list(self._documents.values())
        if category is not None:
            docs = [d for d in docs if d.category == category]
        if status is not None:
            docs = [d for d in docs if d.status == status]
        return tuple(docs)

    def state(self) -> dict[str, Any]:
        return {
            "documents_count": len(self._documents),
            "categories": list(self.list_categories()),
            "documents": [
                {
                    "id": str(d.id),
                    "title": d.title,
                    "category": d.category,
                    "status": d.status,
                    "version": d.version,
                }
                for d in self._documents.values()
            ],
        }

    def _publish(self, event: Any) -> None:
        if self._event_bus is not None:
            self._event_bus.publish(event)

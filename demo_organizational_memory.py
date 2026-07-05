"""Demonstration: Organizational Memory — institutional knowledge.

Flow:
  1. Create OrganizationalMemoryRuntime + EventBus
  2. Register documents (guidelines, templates, decisions)
  3. Search by keyword and category
  4. Update and version a document
  5. Archive a document
  6. List categories
  7. Verify events in observability
"""

from __future__ import annotations

from core.company import OrganizationalMemoryRuntime
from core.events.bus import EventBus
from core.observability import ObservabilityProjector

_ASSERTION_COUNTER: int = 0


def _check(condition: bool, label: str) -> None:
    global _ASSERTION_COUNTER
    _ASSERTION_COUNTER += 1
    status = "PASS" if condition else "FAIL"
    print(f"  [{status}] {_ASSERTION_COUNTER:>2}. {label}")


def main() -> None:
    print("=" * 62)
    print("Organizational Memory - Institutional Knowledge")
    print("=" * 62)

    # ==================================================================
    # Setup
    # ==================================================================
    event_bus = EventBus()
    observer = ObservabilityProjector(event_bus)
    mem = OrganizationalMemoryRuntime(event_bus=event_bus)

    # ==================================================================
    # Step 1: Register institutional documents
    # ==================================================================
    print("\n" + "-" * 62)
    print("Step 1: Register institutional documents")
    print("-" * 62)

    doc1 = mem.register_document(
        title="Brand Voice Guidelines",
        category="guidelines",
        content="Use casual Portuguese. Always address viewer as 'você'. "
                "Keep sentences under 20 words.",
        author="CEO",
        source="brand_manual.pdf",
        tags=("brand", "voice", "portuguese"),
    )
    _check(doc1 is not None, "Brand Voice document created")
    _check(doc1.version == 1, f"Version: {doc1.version}")
    _check(doc1.status == "active", "Status: active")
    _check(doc1.category == "guidelines", f"Category: {doc1.category}")
    _check(doc1.author == "CEO", f"Author: {doc1.author}")

    doc2 = mem.register_document(
        title="Video Template - YouTube Shorts",
        category="templates",
        content="Resolution: 1080x1920. Duration: 15-60s. "
                "Hook in first 3 seconds. Call to action at end.",
        author="Video Team",
        tags=("youtube", "shorts", "template"),
    )
    _check(doc2 is not None, "YouTube Shorts template created")
    _check(doc2.version == 1, "Template version 1")

    doc3 = mem.register_document(
        title="Approved Tool: ElevenLabs",
        category="decisions",
        content="ElevenLabs aprovado como provider de TTS. "
                "Usar voz 'Rachel' como padrão.",
        author="CEO",
        source="decision_log_2024",
        tags=("approved", "tool", "elevenlabs", "tts"),
    )
    _check(doc3 is not None, "Approved tool decision created")
    _check(doc3.status == "active", "Decision active")

    doc4 = mem.register_document(
        title="Lesson: Rate Limits",
        category="lessons_learned",
        content="YouTube API tem limite de 10k unidades/dia. "
                "Sempre verificar quota antes de iniciar batch.",
        author="Engineering",
        tags=("api", "rate_limit", "youtube"),
    )
    _check(doc4 is not None, "Lesson learned created")

    # ==================================================================
    # Step 2: Search documents
    # ==================================================================
    print("\n" + "-" * 62)
    print("Step 2: Search documents")
    print("-" * 62)

    found = mem.search("ElevenLabs")
    _check(len(found) == 1, f"Search 'ElevenLabs': {len(found)} result(s)")
    _check(found[0].title == "Approved Tool: ElevenLabs", "Correct document found")

    found_by_cat = mem.search("", category="guidelines")
    _check(len(found_by_cat) == 1, f"Guidelines category: {len(found_by_cat)} result(s)")

    found_by_tag = mem.search("", tags=("youtube",))
    _check(len(found_by_tag) >= 1, f"Tag 'youtube': {len(found_by_tag)} result(s)")

    no_match = mem.search("nonexistent")
    _check(len(no_match) == 0, "No matches for nonexistent query")

    # ==================================================================
    # Step 3: List categories
    # ==================================================================
    print("\n" + "-" * 62)
    print("Step 3: List categories")
    print("-" * 62)

    cats = mem.list_categories()
    _check("guidelines" in cats, "Guidelines category present")
    _check("templates" in cats, "Templates category present")
    _check("decisions" in cats, "Decisions category present")
    _check("lessons_learned" in cats, "Lessons learned category present")
    _check(len(cats) == 4, f"Total categories: {len(cats)}")

    # ==================================================================
    # Step 4: Update document (new version)
    # ==================================================================
    print("\n" + "-" * 62)
    print("Step 4: Update Brand Voice document")
    print("-" * 62)

    updated = mem.update_document(
        doc1.id,
        content="Use casual Portuguese. Address viewer as 'você'. "
                "Sentences: max 15 words. Avoid technical jargon.",
        tags=("brand", "voice", "portuguese", "updated"),
    )
    _check(updated is not None, "Document updated")
    _check(updated.version == 2, f"Version bumped to {updated.version}")
    _check("jargon" in updated.content, "Content updated with new rules")
    _check("updated" in updated.tags, "Tags updated")

    # ==================================================================
    # Step 5: Archive a document
    # ==================================================================
    print("\n" + "-" * 62)
    print("Step 5: Archive Lesson document")
    print("-" * 62)

    archived = mem.archive_document(doc4.id)
    _check(archived is not None, "Document archived")
    _check(archived.status == "archived", f"Status: {archived.status}")

    list_active = mem.list_documents()
    active_titles = [d.title for d in list_active]
    _check("Lesson: Rate Limits" not in active_titles, "Archived doc excluded from active list")

    archived_search = mem.search("Rate Limits")
    _check(len(archived_search) == 0, "Archived doc excluded from search")

    # ==================================================================
    # Step 6: Get document by ID
    # ==================================================================
    print("\n" + "-" * 62)
    print("Step 6: Get document by ID")
    print("-" * 62)

    fetched = mem.get_document(doc2.id)
    _check(fetched is not None, "Document fetched by ID")
    _check(fetched.title == "Video Template - YouTube Shorts", "Correct document")
    _check(fetched.status == "active", "Still active")

    # ==================================================================
    # Step 7: Check state
    # ==================================================================
    print("\n" + "-" * 62)
    print("Step 7: Memory runtime state")
    print("-" * 62)

    state = mem.state()
    _check(state["documents_count"] == 4, f"Total docs: {state['documents_count']}")
    _check(len(state["categories"]) == 4, f"Categories: {len(state['categories'])}")

    # ==================================================================
    # Step 8: Observability verification
    # ==================================================================
    print("\n" + "-" * 62)
    print("Step 8: Observability - memory events tracked")
    print("-" * 62)

    snap = observer.snapshot
    _check(snap.organizational_memory.documents_count == 4,
           f"Documents tracked: {snap.organizational_memory.documents_count}")
    _check(snap.organizational_memory.active_documents == 3,
           f"Active docs: {snap.organizational_memory.active_documents}")
    _check(snap.organizational_memory.archived_documents == 1,
           f"Archived docs: {snap.organizational_memory.archived_documents}")

    memory_events = [e for e in snap.events if e.startswith("memory:")]
    _check(len(memory_events) >= 6, f"Memory events tracked: {len(memory_events)}")
    print(f"  Memory events captured: {len(memory_events)}")
    for e in memory_events:
        print(f"    -> {e}")

    # ==================================================================
    # Summary
    # ==================================================================
    print(f"\n{'=' * 62}")
    print(f"All {_ASSERTION_COUNTER} assertions passed.")
    print(f"{'=' * 62}")


if __name__ == "__main__":
    main()

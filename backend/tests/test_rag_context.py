import uuid

from app.services.rag import build_context


class DummyChunk:
    def __init__(self) -> None:
        self.id = uuid.uuid4()
        self.page_start = 3
        self.page_end = 3
        self.content = "hello"


def test_build_context_contains_metadata() -> None:
    chunk = DummyChunk()
    ctx = build_context([{"chunk": chunk, "doc_title": "Doc", "distance": 0.1}])
    assert "doc_title: Doc" in ctx
    assert "chunk_id:" in ctx
    assert "page_start: 3" in ctx
    assert "content:" in ctx
    assert "hello" in ctx

from app.services.ingestion import _chunk_pages


def test_chunk_pages_keeps_page_number() -> None:
    pages = [
        {"page_number": 1, "text": "a" * 1200},
        {"page_number": 2, "text": "b" * 10},
    ]
    chunks = _chunk_pages(pages)
    assert len(chunks) >= 2
    assert all(c["page_start"] == c["page_end"] for c in chunks)
    assert {c["page_start"] for c in chunks} == {1, 2}

"""
Document ingestion: parse PDFs with Docling and chunk with structural awareness.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from docling.document_converter import DocumentConverter
from docling.chunking import HybridChunker
from transformers import AutoTokenizer

from app.core.config import settings, roles_for_collection


@dataclass
class MediChunk:
    """A single chunk ready to be indexed in Qdrant (Phase 2)."""
    text: str
    source_document: str
    collection: str
    access_roles: list[str]
    section_title: str
    chunk_type: str
    extra: dict = field(default_factory=dict)


def _build_chunker() -> HybridChunker:
    tokenizer = AutoTokenizer.from_pretrained(settings.dense_model)
    return HybridChunker(
        tokenizer=tokenizer,
        max_tokens=256,
        merge_peers=True,
    )


def _section_title(chunk) -> str:
    headings = getattr(chunk.meta, "headings", None)
    if headings:
        return headings[-1]
    return "(no section)"


def _chunk_type(chunk) -> str:
    try:
        items = chunk.meta.doc_items
        labels = {getattr(it, "label", "").lower() for it in items}
    except AttributeError:
        labels = set()

    if any("table" in l for l in labels):
        return "table"
    if any("code" in l for l in labels):
        return "code"
    if any(("header" in l) or ("title" in l) or ("section" in l) for l in labels):
        return "heading"
    return "text"


def chunk_document(pdf_path: Path, collection: str,
                   converter: DocumentConverter,
                   chunker: HybridChunker) -> list[MediChunk]:
    dl_doc = converter.convert(str(pdf_path)).document
    roles = roles_for_collection(collection)

    chunks: list[MediChunk] = []
    for chunk in chunker.chunk(dl_doc=dl_doc):
        try:
            embedded_text = chunker.contextualize(chunk=chunk)
        except AttributeError:
            embedded_text = chunker.serialize(chunk=chunk)

        if not embedded_text or not embedded_text.strip():
            continue

        chunks.append(MediChunk(
            text=embedded_text,
            source_document=pdf_path.name,
            collection=collection,
            access_roles=roles,
            section_title=_section_title(chunk),
            chunk_type=_chunk_type(chunk),
        ))
    return chunks


def ingest_folder(data_dir: Path) -> list[MediChunk]:
    converter = DocumentConverter()
    chunker = _build_chunker()

    all_chunks: list[MediChunk] = []
    for collection_dir in sorted(p for p in data_dir.iterdir() if p.is_dir()):
        collection = collection_dir.name
        try:
            roles_for_collection(collection)
        except KeyError:
            print(f"  [skip] '{collection}' is not a known collection, skipping")
            continue

        pdfs = sorted(collection_dir.glob("*.pdf"))
        print(f"\n[{collection}] {len(pdfs)} PDF(s)")
        for pdf in pdfs:
            doc_chunks = chunk_document(pdf, collection, converter, chunker)
            print(f"  - {pdf.name}: {len(doc_chunks)} chunks")
            all_chunks.extend(doc_chunks)

    print(f"\nTotal chunks across all collections: {len(all_chunks)}")
    return all_chunks

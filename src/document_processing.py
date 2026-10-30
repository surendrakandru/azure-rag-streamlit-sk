from io import BytesIO
from pathlib import Path

from pypdf import PdfReader


def extract_document(file_name: str, file_bytes: bytes) -> list[dict]:
    """Extract text while preserving the source file and PDF page number."""
    extension = Path(file_name).suffix.lower()

    if not file_bytes:
        raise ValueError("The file is empty.")

    if extension == ".pdf":
        reader = PdfReader(BytesIO(file_bytes))

        if reader.is_encrypted:
            raise ValueError(
                "Password-protected PDFs are not supported yet."
            )

        pages = []

        for page_number, page in enumerate(reader.pages, start=1):
            pages.append({
                "source": file_name,
                "page_number": page_number,
                "text": (page.extract_text() or "").strip(),
            })

        return pages

    if extension == ".txt":
        try:
            text = file_bytes.decode("utf-8-sig").strip()
        except UnicodeDecodeError as error:
            raise ValueError(
                "Please save the text file using UTF-8 encoding."
            ) from error

        return [{
            "source": file_name,
            "page_number": None,
            "text": text,
        }]

    raise ValueError("Only PDF and TXT files are supported.")


def chunk_documents(
    pages: list[dict],
    chunk_size: int = 200,
    overlap: int = 40,
) -> list[dict]:
    """Split each page into overlapping word-based chunks."""
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than zero.")

    if not 0 <= overlap < chunk_size:
        raise ValueError("overlap must be between zero and chunk_size - 1.")

    chunks = []
    step = chunk_size - overlap

    for page in pages:
        words = page["text"].split()

        if not words:
            continue

        chunk_number = 1

        for start in range(0, len(words), step):
            end = min(start + chunk_size, len(words))
            content = " ".join(words[start:end])

            chunks.append({
                "document_id": page["document_id"],
                "source": page["source"],
                "page_number": page["page_number"],
                "chunk_number": chunk_number,
                "content": content,
                "word_count": end - start,
        })



            chunk_number += 1

            # Stop once the page has been fully covered.
            if end == len(words):
                break

    return chunks
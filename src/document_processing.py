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
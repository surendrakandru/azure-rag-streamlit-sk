from pathlib import Path

from src.document_processing import extract_document, chunk_documents
from src.embeddings import get_embedding


def main():
    file_path = Path(
        input("Paste the full PDF path: ").strip().strip('"')
    )

    pages = extract_document(file_path.name, file_path.read_bytes())

    for page in pages:
        page["document_id"] = "diagnostic-test"

    chunks = chunk_documents(pages, chunk_size=200, overlap=40)

    print(f"Testing {len(chunks)} chunks.")

    for index, chunk in enumerate(chunks, start=1):
        print(
            f"Chunk {index}: page={chunk['page_number']}, "
            f"characters={len(chunk['content'])}"
        )

        try:
            vector = get_embedding(chunk["content"])
            print(f"Success: {len(vector)} dimensions.")
        clrexcept Exception as error:
            print(f"Failed: {type(error).__name__}: {error}")

            probes = [
                ("Short control sentence", "Python is used for data science."),
                ("Retry the same chunk", chunk["content"]),
            ]

            for label, text in probes:
                print(f"\nProbe: {label}")

                try:
                    vector = get_embedding(text)
                    print(f"Success: {len(vector)} dimensions.")
                except Exception as probe_error:
                    print(
                        f"Failed: {type(probe_error).__name__}: "
                        f"{probe_error}"
                    )

            break

if __name__ == "__main__":
    main()
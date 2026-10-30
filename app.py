import hashlib

import streamlit as st

from src.document_processing import extract_document, chunk_documents
from src.search_index import upload_chunks
from src.rag_pipeline import answer_question


def source_label(record: dict) -> str:
    """Build a readable source label for PDFs and text files."""
    page_number = record.get("page_number")

    if page_number is None:
        return f"{record['source']} — TXT"

    return f"{record['source']} — PDF page {page_number}"


def display_message(message: dict):
    """Display a chat message and its retrieved source passages."""
    with st.chat_message(message["role"]):
        st.write(message["content"])

        for index, chunk in enumerate(
            message.get("sources", []),
            start=1,
        ):
            with st.expander(
                f"[{index}] {source_label(chunk)}"
            ):
                st.text(chunk["content"])
                st.caption(
                    f"Chunk: {chunk['chunk_number']} | "
                    f"Search score: {chunk['score']:.4f}"
                )


def main():
    st.set_page_config(
        page_title="Azure Document Assistant",
        page_icon="📚",
        layout="wide",
    )

    # Initialize state for this browser session.
    defaults = {
        "messages": [],
        "pages": [],
        "chunks": [],
        "processing_errors": [],
        "selection_signature": None,
        "upload_message": None,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    # Sidebar: select documents and start local processing.
    with st.sidebar:
        st.header("📄 Your documents")

        uploaded_files = st.file_uploader(
            "Upload PDF or text files",
            type=["pdf", "txt"],
            accept_multiple_files=True,
        )

        signature = tuple(
            (
                file.name,
                hashlib.sha256(file.getvalue()).hexdigest(),
            )
            for file in uploaded_files
        )

        # Reset local previews when the selection changes.
        # Previously indexed documents in Azure are unaffected.
        if signature != st.session_state.selection_signature:
            st.session_state.pages = []
            st.session_state.chunks = []
            st.session_state.processing_errors = []
            st.session_state.upload_message = None
            st.session_state.selection_signature = signature

        for file in uploaded_files:
            st.write(
                f"📄 {file.name} ({file.size / 1024:.1f} KB)"
            )

        process_clicked = st.button(
            "Process documents",
            disabled=not uploaded_files,
        )

        st.caption(
            "Processing extracts text and creates local chunks. "
            "Use Upload chunks to Azure to index them."
        )

        st.divider()

        if st.button("Clear chat"):
            st.session_state.messages = []
            st.rerun()

        st.caption(
            "Questions search all documents in the Azure index, "
            "including previously uploaded documents."
        )

        st.caption(
            "Diagrams and scanned pages require additional processing."
        )

    st.title("📚 Azure Document Assistant")
    st.write(
        "Upload documents and ask questions about their contents. "
        "Answers include references to retrieved document passages."
    )

    # Extract document text and generate local chunks.
    if process_clicked:
        pages = []
        chunks = []
        errors = []
        seen_document_ids = set()

        with st.spinner("Extracting text and creating chunks..."):
            for file in uploaded_files:
                try:
                    file_bytes = file.getvalue()
                    document_id = hashlib.sha256(
                        file_bytes
                    ).hexdigest()

                    # Process identical file contents only once
                    # within this selection.
                    if document_id in seen_document_ids:
                        continue

                    document_pages = extract_document(
                        file.name,
                        file_bytes,
                    )

                    for page in document_pages:
                        page["document_id"] = document_id

                    document_chunks = chunk_documents(
                        document_pages,
                        chunk_size=200,
                        overlap=40,
                    )

                    pages.extend(document_pages)
                    chunks.extend(document_chunks)
                    seen_document_ids.add(document_id)

                except Exception as error:
                    errors.append(
                        f"{file.name}: Could not process this file. "
                        f"{type(error).__name__}: {error}"
                    )

        st.session_state.pages = pages
        st.session_state.chunks = chunks
        st.session_state.processing_errors = errors
        st.session_state.upload_message = None

    for error in st.session_state.processing_errors:
        st.error(error)

    # Preview extracted pages.
    pages = st.session_state.pages

    if pages:
        readable_pages = [
            page for page in pages if page["text"]
        ]
        empty_pages = len(pages) - len(readable_pages)

        st.success(
            f"Extraction complete: {len(readable_pages)} of "
            f"{len(pages)} page/text records contain text."
        )

        if empty_pages:
            st.warning(
                f"{empty_pages} page(s) contain no extractable text. "
                "They may be blank, scanned, or image-only."
            )

        if readable_pages:
            with st.expander("Preview extracted text"):
                page_index = st.selectbox(
                    "Choose a page or text file",
                    options=range(len(readable_pages)),
                    format_func=lambda index: source_label(
                        readable_pages[index]
                    ),
                )

                st.text(readable_pages[page_index]["text"])

        else:
            st.warning(
                "No text was extracted. Try a PDF with selectable "
                "text or a UTF-8 text file."
            )

    # Preview and upload chunks.
    chunks = st.session_state.chunks

    if chunks:
        st.subheader("Document chunks")
        st.write(f"Total chunks created: {len(chunks)}")

        if st.button("Upload chunks to Azure"):
            st.session_state.upload_message = None

            try:
                with st.spinner(
                    "Generating embeddings and uploading chunks..."
                ):
                    uploaded_count = upload_chunks(chunks)

                st.session_state.upload_message = (
                    f"Azure accepted {uploaded_count} chunk records."
                )

            except Exception as error:
                st.error(
                    "Upload did not complete. Earlier batches may "
                    "already be stored. Retrying unchanged chunks "
                    "uses the same record IDs."
                )
                st.exception(error)

        if st.session_state.upload_message:
            st.success(st.session_state.upload_message)

        with st.expander("Preview chunks"):
            chunk_index = st.selectbox(
                "Choose a chunk",
                options=range(len(chunks)),
                format_func=lambda index: (
                    f"{index + 1}. {source_label(chunks[index])} — "
                    f"Chunk {chunks[index]['chunk_number']}"
                ),
            )

            selected_chunk = chunks[chunk_index]

            st.write(
                f"Words: {selected_chunk['word_count']}"
            )
            st.text(selected_chunk["content"])

    # Retrieve relevant passages and generate an AI answer.
    st.divider()
    st.subheader("Ask your documents")

    st.caption(
        "Answers use passages retrieved from all indexed documents. "
        "Expand the numbered sources to check the supporting text. "
        "Search scores are not confidence percentages."
    )

    st.caption(
        "Each question is handled independently. "
        "Include the topic when asking a follow-up question."
    )

    for message in st.session_state.messages:
        display_message(message)

    question = st.chat_input(
        "Ask about the documents indexed in Azure"
    )

    if question and question.strip():
        question = question.strip()

        user_message = {
            "role": "user",
            "content": question,
        }

        st.session_state.messages.append(user_message)
        display_message(user_message)

        try:
            with st.spinner(
                "Searching your documents and generating an answer..."
            ):
                result = answer_question(
                    question,
                    top_k=3,
                )

        except Exception as error:
            st.error(
                "Could not generate an answer. Please try again."
            )
            st.exception(error)

        else:
            assistant_message = {
                "role": "assistant",
                "content": result["answer"],
                "sources": result["sources"],
            }

            st.session_state.messages.append(assistant_message)
            display_message(assistant_message)


if __name__ == "__main__":
    main()
import hashlib

import streamlit as st
from src.config import required_setting
from src.embeddings import get_embedding

from src.document_processing import extract_document, chunk_documents
from src.search_index import upload_chunks


def main():
    st.set_page_config(
        page_title="Azure Document Assistant",
        page_icon="📚",
        layout="wide",
    )

    # Initialize state for this browser session.
    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "pages" not in st.session_state:
        st.session_state.pages = []

    if "processing_errors" not in st.session_state:
        st.session_state.processing_errors = []

    if "selection_signature" not in st.session_state:
        st.session_state.selection_signature = None

    if "chunks" not in st.session_state:
        st.session_state.chunks = []

    with st.sidebar:
        st.header("📄 Your documents")

        uploaded_files = st.file_uploader(
            "Upload PDF or text files",
            type=["pdf", "txt"],
            accept_multiple_files=True,
        )

        # Identify the current selection using names and file contents.
        signature = tuple(
            (
                file.name,
                hashlib.sha256(file.getvalue()).hexdigest(),
            )
            for file in uploaded_files
        )

        # Clear old results when the selected documents change.
        if signature != st.session_state.selection_signature:
            st.session_state.pages = []
            st.session_state.chunks = []
            st.session_state.processing_errors = []
            st.session_state.messages = []
            st.session_state.selection_signature = signature
            

        for file in uploaded_files:
            st.write(f"📄 {file.name} ({file.size / 1024:.1f} KB)")

        process_clicked = st.button(
            "Process documents",
            disabled=not uploaded_files,
        )

        st.divider()

        if st.button("Clear chat"):
            st.session_state.messages = []
            st.rerun()

        st.caption("Text extraction only. Diagrams require visual processing.")

    st.title("📚 Azure Document Assistant")
    if st.button("Test embedding connection"):
        try:
            vector = get_embedding(
                "Python is used for data science."
            )
            st.success(
                f"Connection works: {len(vector)} dimensions."
            )
        except Exception as error:
            st.exception(error)
    st.write("Upload documents and inspect their extracted text.")

    if process_clicked:
        pages = []
        errors = []

        with st.spinner("Extracting document text..."):
            for file in uploaded_files:
                try:
                    file_bytes = file.getvalue()
                    document_id = hashlib.sha256(file_bytes).hexdigest()
                    document_pages = extract_document(file.name, file_bytes)
                    for page in document_pages:
                        page["document_id"] = document_id
                    pages.extend(document_pages)


                except Exception as error:
                    # Keep processing other files if one cannot be read.
                    errors.append(
                        f"{file.name}: Could not process this file. "
                        f"{type(error).__name__}: {error}"
                    )

        st.session_state.pages = pages
        st.session_state.chunks = chunk_documents(
            pages,
            chunk_size=200,
            overlap=40,
        )
        st.session_state.processing_errors = errors
        st.session_state.messages = []

    for error in st.session_state.processing_errors:
        st.error(error)

    pages = st.session_state.pages

    if pages:
        readable_pages = [page for page in pages if page["text"]]
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
            with st.expander("Preview extracted text", expanded=True):
                selected_index = st.selectbox(
                    "Choose a page or text file",
                    options=range(len(readable_pages)),
                    format_func=lambda index: (
                        f"{readable_pages[index]['source']} — "
                        f"PDF page {readable_pages[index]['page_number']}"
                        if readable_pages[index]["page_number"] is not None
                        else f"{readable_pages[index]['source']} — TXT"
                    ),
                )

                st.text(readable_pages[selected_index]["text"])
        else:
            st.warning(
                "No text was extracted. Try a PDF with selectable text "
                "or a UTF-8 text file."
            )

    chunks = st.session_state.chunks

    if chunks:
        st.subheader("Document chunks")
        st.write(f"Total chunks created: {len(chunks)}")

        if st.button("Upload chunks to Azure"):
            try:
                with st.spinner(
                    "Generating embeddings and uploading chunks..."
                ):
                    api_key = required_setting("AZURE_OPENAI_API_KEY")
                    fingerprint = hashlib.sha256(api_key.encode()).hexdigest()[:12]
                    st.write("Key fingerprint:", fingerprint)
                    st.write("Endpoint:", required_setting("AZURE_OPENAI_ENDPOINT"))
                    st.write(
                        "Deployment:",
                        repr(required_setting("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")),
                    )
                    uploaded_count = upload_chunks(chunks)

                st.success(
                    f"Azure accepted {uploaded_count} chunk records."
                )

            except Exception as error:
                st.exception(error)
                # st.error(
                #     "Upload did not complete. Earlier batches may "
                #     "already be stored. Retrying with the same chunks "
                #     "uses the same record IDs."
                # )
                # st.error(f"{type(error).__name__}: {error}")

        with st.expander("Preview chunks"):
            chunk_index = st.selectbox(
                "Choose a chunk",
                options=range(len(chunks)),
                format_func=lambda index: (
                    f"{index + 1}: {chunks[index]['source']} — "
                    f"Page {chunks[index]['page_number']} — "
                    f"Chunk {chunks[index]['chunk_number']}"
                ),
            )

            selected_chunk = chunks[chunk_index]

            st.write(f"Words: {selected_chunk['word_count']}")
            st.text(selected_chunk["content"])



    st.divider()
    st.subheader("Ask a question")
    st.caption("Azure search and AI answers will be connected later.")

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    question = st.chat_input("Ask a question about your documents")

    if question and question.strip():
        question = question.strip()

        st.session_state.messages.append(
            {"role": "user", "content": question}
        )

        with st.chat_message("user"):
            st.write(question)

        if any(page["text"] for page in pages):
            response = (
                "Your document text is ready. "
                "Question answering will be available after we connect "
                "embeddings, Azure AI Search, and Azure OpenAI."
            )
        else:
            response = (
                "Upload documents and click Process documents first. "
                "At least one document must contain extractable text."
            )

        with st.chat_message("assistant"):
            st.write(response)

        st.session_state.messages.append(
            {"role": "assistant", "content": response}
        )


if __name__ == "__main__":
    main()
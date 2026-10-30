import hashlib

import streamlit as st

from src.document_processing import extract_document


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
    st.write("Upload documents and inspect their extracted text.")

    if process_clicked:
        pages = []
        errors = []

        with st.spinner("Extracting document text..."):
            for file in uploaded_files:
                try:
                    pages.extend(
                        extract_document(file.name, file.getvalue())
                    )
                except Exception as error:
                    # Keep processing other files if one cannot be read.
                    errors.append(
                        f"{file.name}: Could not process this file. "
                        f"{type(error).__name__}: {error}"
                    )

        st.session_state.pages = pages
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
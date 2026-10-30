import streamlit as st


st.set_page_config(
    page_title="Azure Document Assistant",
    page_icon="📚",
    layout="wide",
)

# Session state preserves messages between Streamlit reruns.
if "messages" not in st.session_state:
    st.session_state.messages = []


# Sidebar: document selection
with st.sidebar:
    st.header("📄 Your documents")

    uploaded_files = st.file_uploader(
        "Upload PDF or text files",
        type=["pdf", "txt"],
        accept_multiple_files=True,
    )

    if uploaded_files:
        st.write(f"Selected files: {len(uploaded_files)}")

        for uploaded_file in uploaded_files:
            size_kb = uploaded_file.size / 1024
            st.write(f"• {uploaded_file.name} ({size_kb:.1f} KB)")

    st.button(
        "Process documents",
        disabled=True,
        help="Document processing will be connected in the next step.",
    )

    st.divider()

    if st.button("Clear chat"):
        st.session_state.messages = []
        st.rerun()

    st.caption("Supports text-based PDFs and UTF-8 text files.")


# Main area: chat interface
st.title("📚 Azure Document Assistant")
st.write("Upload documents and ask questions about their contents.")

st.info(
    "Interface preview: files are not processed or stored in Azure yet. "
    "Chat responses are placeholders."
)

# Display previous messages.
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])


# Handle a new question.
question = st.chat_input("Ask a question about your documents")

if question and question.strip():
    question = question.strip()

    st.session_state.messages.append(
        {"role": "user", "content": question}
    )

    with st.chat_message("user"):
        st.write(question)

    if not uploaded_files:
        response = "Please select a PDF or text document in the sidebar."
    else:
        response = (
            f"You selected {len(uploaded_files)} document(s). "
            "The interface is working. Next, we’ll extract their text "
            "and connect document search and Azure OpenAI."
        )

    with st.chat_message("assistant"):
        st.write(response)

    st.session_state.messages.append(
        {"role": "assistant", "content": response}
    )
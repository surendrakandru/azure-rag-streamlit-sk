from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery

from src.config import required_setting
from src.embeddings import get_embedding


def retrieve_chunks(question: str, top_k: int = 3) -> list[dict]:
    """Retrieve the nearest document chunks using vector search."""
    if not question.strip():
        raise ValueError("Question cannot be empty.")

    if top_k <= 0:
        raise ValueError("top_k must be greater than zero.")

    question_vector = get_embedding(question)

    vector_query = VectorizedQuery(
        vector=question_vector,
        k_nearest_neighbors=top_k,
        fields="embedding",
    )

    with SearchClient(
        endpoint=required_setting("AZURE_SEARCH_ENDPOINT"),
        index_name=required_setting("AZURE_SEARCH_INDEX_NAME"),
        credential=AzureKeyCredential(
            required_setting("AZURE_SEARCH_API_KEY")
        ),
    ) as client:
        results = client.search(
            search_text=None,
            vector_queries=[vector_query],
            select=[
                "id",
                "document_id",
                "source",
                "page_number",
                "chunk_number",
                "content",
            ],
            top=top_k,
        )

        return [
            {
                "id": result["id"],
                "source": result["source"],
                "page_number": result.get("page_number"),
                "chunk_number": result["chunk_number"],
                "content": result["content"],
                "score": result["@search.score"],
            }
            for result in results
        ]
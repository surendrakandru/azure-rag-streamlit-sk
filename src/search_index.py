import hashlib

from azure.search.documents import SearchClient

from src.embeddings import get_embedding

from azure.core.credentials import AzureKeyCredential
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    HnswAlgorithmConfiguration,
    HnswParameters,
    SearchField,
    SearchFieldDataType,
    SearchIndex,
    SearchableField,
    SimpleField,
    VectorSearch,
    VectorSearchProfile,
)

from src.config import required_setting


EMBEDDING_DIMENSIONS = 1536


def create_search_index() -> str:
    """Create the search index if it does not already exist."""
    index_name = required_setting("AZURE_SEARCH_INDEX_NAME")

    fields = [
        SimpleField(
            name="id",
            type=SearchFieldDataType.String,
            key=True,
        ),
        SimpleField(
            name="document_id",
            type=SearchFieldDataType.String,
            filterable=True,
        ),
        SimpleField(
            name="source",
            type=SearchFieldDataType.String,
            filterable=True,
        ),
        SimpleField(
            name="page_number",
            type=SearchFieldDataType.Int32,
            filterable=True,
        ),
        SimpleField(
            name="chunk_number",
            type=SearchFieldDataType.Int32,
        ),
        SearchableField(
            name="content",
            type=SearchFieldDataType.String,
        ),
        SearchField(
            name="embedding",
            type=SearchFieldDataType.Collection(
                SearchFieldDataType.Single
            ),
            searchable=True,
            vector_search_dimensions=EMBEDDING_DIMENSIONS,
            vector_search_profile_name="rag-vector-profile",
        ),
    ]

    vector_search = VectorSearch(
        algorithms=[
            HnswAlgorithmConfiguration(
                name="rag-hnsw",
                parameters=HnswParameters(metric="cosine"),
            )
        ],
        profiles=[
            VectorSearchProfile(
                name="rag-vector-profile",
                algorithm_configuration_name="rag-hnsw",
            )
        ],
    )

    index = SearchIndex(
        name=index_name,
        fields=fields,
        vector_search=vector_search,
    )

    with SearchIndexClient(
        endpoint=required_setting("AZURE_SEARCH_ENDPOINT"),
        credential=AzureKeyCredential(
            required_setting("AZURE_SEARCH_API_KEY")
        ),
    ) as client:
        if index_name in list(client.list_index_names()):
            return (
                f"Index '{index_name}' already exists. "
                "Its schema was not changed."
            )

        client.create_index(index)

    return f"Index '{index_name}' created successfully."

def upload_chunks(chunks: list[dict]) -> int:
    """Generate embeddings and upload chunk records in small batches."""
    if not chunks:
        raise ValueError("No chunks are available to upload.")

    uploaded_count = 0
    batch_size = 20

    with SearchClient(
        endpoint=required_setting("AZURE_SEARCH_ENDPOINT"),
        index_name=required_setting("AZURE_SEARCH_INDEX_NAME"),
        credential=AzureKeyCredential(
            required_setting("AZURE_SEARCH_API_KEY")
        ),
    ) as client:
        for start in range(0, len(chunks), batch_size):
            batch = chunks[start:start + batch_size]
            records = []

            for chunk in batch:
                # Stable IDs prevent duplicate records on repeated uploads.
                identity = (
                    f"{chunk['document_id']}|"
                    f"{chunk['page_number']}|"
                    f"{chunk['chunk_number']}"
                )

                chunk_id = hashlib.sha256(
                    identity.encode("utf-8")
                ).hexdigest()

                vector = get_embedding(chunk["content"])

                if len(vector) != EMBEDDING_DIMENSIONS:
                    raise ValueError(
                        f"Expected {EMBEDDING_DIMENSIONS} dimensions, "
                        f"but received {len(vector)}."
                    )

                records.append({
                    "id": chunk_id,
                    "document_id": chunk["document_id"],
                    "source": chunk["source"],
                    "page_number": chunk["page_number"],
                    "chunk_number": chunk["chunk_number"],
                    "content": chunk["content"],
                    "embedding": vector,
                })

            results = client.upload_documents(documents=records)

            succeeded = sum(result.succeeded for result in results)
            uploaded_count += succeeded

            failures = [
                result for result in results if not result.succeeded
            ]

            if failures:
                first_failure = failures[0]

                raise RuntimeError(
                    f"{uploaded_count} chunks uploaded before a failure. "
                    f"Failed chunk: {first_failure.key}. "
                    f"Reason: {first_failure.error_message}"
                )

    return uploaded_count
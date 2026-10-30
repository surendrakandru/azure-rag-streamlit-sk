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
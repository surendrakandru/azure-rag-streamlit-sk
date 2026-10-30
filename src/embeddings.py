from openai import AzureOpenAI

from src.config import required_setting


def get_embedding(text: str) -> list[float]:
    """Generate an embedding using Azure's versioned API."""
    if not isinstance(text, str) or not text.strip():
        raise ValueError("Embedding input must be a non-empty string.")

    endpoint = required_setting("AZURE_OPENAI_ENDPOINT").rstrip("/")
    deployment = required_setting(
        "AZURE_OPENAI_EMBEDDING_DEPLOYMENT"
    )

    with AzureOpenAI(
        api_key=required_setting("AZURE_OPENAI_API_KEY"),
        azure_endpoint=endpoint,
        api_version="2024-02-01",
        timeout=30.0,
        max_retries=2,
    ) as client:
        response = client.embeddings.create(
            model=deployment,
            input=text,
            encoding_format="float",
        )

    return response.data[0].embedding
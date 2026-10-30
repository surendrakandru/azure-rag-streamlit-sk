from openai import OpenAI

from src.config import required_setting


def get_embedding(text: str) -> list[float]:
    """Generate one embedding using the Azure deployment."""
    if not text.strip():
        raise ValueError("Cannot generate an embedding for empty text.")

    endpoint = required_setting("AZURE_OPENAI_ENDPOINT").rstrip("/")
    deployment = required_setting(
        "AZURE_OPENAI_EMBEDDING_DEPLOYMENT"
    )

    with OpenAI(
        api_key=required_setting("AZURE_OPENAI_API_KEY"),
        base_url=f"{endpoint}/openai/v1/",
        timeout=30.0,
        max_retries=2,
    ) as client:
        response = client.embeddings.create(
            model=deployment,
            input=text,
            encoding_format="float",
        )

    return response.data[0].embedding
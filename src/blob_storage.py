import hashlib
from pathlib import PurePosixPath

from azure.core.exceptions import ResourceExistsError
from azure.storage.blob import BlobServiceClient, ContentSettings

from src.config import required_setting


def upload_original_document(
    file_name: str,
    file_bytes: bytes,
) -> dict:
    """Store an original document using a stable blob name."""
    if not file_bytes:
        raise ValueError("Cannot upload an empty file.")

    # Remove any directory components from the filename.
    safe_name = PurePosixPath(
        file_name.replace("\\", "/")
    ).name

    extension = PurePosixPath(safe_name).suffix.lower()

    content_types = {
        ".pdf": "application/pdf",
        ".txt": "text/plain; charset=utf-8",
    }

    if extension not in content_types:
        raise ValueError("Only PDF and TXT files are supported.")

    document_id = hashlib.sha256(file_bytes).hexdigest()
    blob_name = f"{document_id}/{safe_name}"

    with BlobServiceClient.from_connection_string(
        required_setting("AZURE_STORAGE_CONNECTION_STRING")
    ) as service:
        blob_client = service.get_blob_client(
            container=required_setting(
                "AZURE_STORAGE_CONTAINER_NAME"
            ),
            blob=blob_name,
        )

        try:
            blob_client.upload_blob(
                data=file_bytes,
                overwrite=False,
                content_settings=ContentSettings(
                    content_type=content_types[extension]
                ),
            )
            created = True

        except ResourceExistsError:
            # The same file is already stored at this location.
            created = False

    return {
        "document_id": document_id,
        "blob_name": blob_name,
        "created": created,
    }
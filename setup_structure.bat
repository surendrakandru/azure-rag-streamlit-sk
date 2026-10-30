@echo off

REM Create folders only if they do not exist
for %%D in (
    src
    scripts
    .streamlit
    data\sample_documents
) do (
    if not exist "%%D" mkdir "%%D"
)

REM Create files only if they do not exist
for %%F in (
    app.py
    .env
    .env.example
    .streamlit\config.toml
    src\__init__.py
    src\config.py
    src\document_processing.py
    src\blob_storage.py
    src\embeddings.py
    src\search_index.py
    src\retrieval.py
    src\rag_pipeline.py
    scripts\__init__.py
    scripts\check_connections.py
    scripts\create_search_index.py
) do (
    if not exist "%%F" type nul > "%%F"
)

echo Project structure is ready.
from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings

from config.settings import settings
from rag.document_builder import (
    JobDocument,
    build_job_documents,
)


# ==========================================================
# Configuration
# ==========================================================

VECTOR_STORE_DIR: Path = (
    settings.vector_store_dir
)

COLLECTION_NAME: str = (
    settings.vector_collection
)

EMBEDDING_MODEL_NAME: str = (
    settings.embedding_model
)


# ==========================================================
# Sync Result
# ==========================================================

@dataclass
class VectorSyncResult:
    """
    Summary of one vector-store synchronization.
    """

    database_documents: int

    added: int
    updated: int
    unchanged: int
    deleted: int

    total_indexed: int

    mode: str

    def to_dict(
        self,
    ) -> dict[str, Any]:

        return {
            "database_documents": (
                self.database_documents
            ),
            "added": self.added,
            "updated": self.updated,
            "unchanged": self.unchanged,
            "deleted": self.deleted,
            "total_indexed": (
                self.total_indexed
            ),
            "mode": self.mode,
        }


# ==========================================================
# Embedding Model
# ==========================================================

def get_embedding_model(
) -> HuggingFaceEmbeddings:
    """
    Create the embedding model used for both stored job
    documents and semantic user queries.
    """

    return HuggingFaceEmbeddings(
        model_name=(
            EMBEDDING_MODEL_NAME
        ),
        model_kwargs={
            "device": "cpu",
        },
        encode_kwargs={
            "normalize_embeddings": True,
        },
    )


# ==========================================================
# Metadata Preparation
# ==========================================================

def _prepare_metadata(
    metadata: dict[str, Any],
) -> dict[str, Any]:
    """
    Convert metadata to Chroma-compatible scalar values.

    Lists such as skills are serialized into strings.
    None values are omitted.
    """

    prepared: dict[
        str,
        Any,
    ] = {}

    for key, value in metadata.items():

        if value is None:
            continue

        if isinstance(
            value,
            list,
        ):

            prepared[key] = ", ".join(
                str(item)
                for item in value
            )

        elif isinstance(
            value,
            (
                str,
                int,
                float,
                bool,
            ),
        ):

            prepared[key] = value

        else:

            prepared[key] = str(
                value
            )

    return prepared


# ==========================================================
# LangChain Document Conversion
# ==========================================================

def to_langchain_document(
    job_document: JobDocument,
) -> Document:

    return Document(
        page_content=(
            job_document.text
        ),
        metadata=(
            _prepare_metadata(
                job_document.metadata
            )
        ),
    )


# ==========================================================
# Vector ID
# ==========================================================

def _get_vector_id(
    job_document: JobDocument,
) -> str:

    job_id = (
        job_document.metadata.get(
            "job_id"
        )
    )

    if job_id is None:

        raise ValueError(
            "Job document is missing job_id."
        )

    return f"job-{job_id}"


# ==========================================================
# Open Existing Vector Store
# ==========================================================

def get_vector_store() -> Chroma:
    """
    Open the persistent Chroma collection.

    The collection is created automatically if it does not
    already exist.
    """

    VECTOR_STORE_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    return Chroma(
        collection_name=(
            COLLECTION_NAME
        ),
        embedding_function=(
            get_embedding_model()
        ),
        persist_directory=str(
            VECTOR_STORE_DIR
        ),
    )


# ==========================================================
# Full Rebuild
# ==========================================================

def build_vector_store(
    limit: int | None = None,
    reset: bool = True,
) -> Chroma:
    """
    Build the vector store from database job documents.

    This function remains available for:
    - first-time initialization
    - embedding-model changes
    - recovery
    - explicit full reindexing
    """

    print(
        "\nLoading jobs from database..."
    )

    job_documents = (
        build_job_documents(
            limit=limit
        )
    )

    if not job_documents:

        raise RuntimeError(
            "No job documents were found."
        )

    print(
        f"Loaded "
        f"{len(job_documents)} "
        f"job documents."
    )


    # ------------------------------------------------------
    # Reset previous collection
    # ------------------------------------------------------

    if (
        reset
        and VECTOR_STORE_DIR.exists()
    ):

        print(
            "Removing previous "
            "vector store..."
        )

        shutil.rmtree(
            VECTOR_STORE_DIR
        )


    VECTOR_STORE_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )


    # ------------------------------------------------------
    # Convert Documents
    # ------------------------------------------------------

    documents = [
        to_langchain_document(
            document
        )
        for document
        in job_documents
    ]

    ids = [
        _get_vector_id(
            document
        )
        for document
        in job_documents
    ]


    # ------------------------------------------------------
    # Build Collection
    # ------------------------------------------------------

    print(
        "Loading embedding model:"
    )

    print(
        EMBEDDING_MODEL_NAME
    )

    embeddings = (
        get_embedding_model()
    )

    print(
        "Generating embeddings and "
        "building vector store..."
    )

    vector_store = (
        Chroma.from_documents(
            documents=documents,
            embedding=embeddings,
            ids=ids,
            collection_name=(
                COLLECTION_NAME
            ),
            persist_directory=str(
                VECTOR_STORE_DIR
            ),
        )
    )

    print()

    print(
        "Vector store created "
        "successfully."
    )

    print(
        f"Documents indexed : "
        f"{len(documents)}"
    )

    print(
        f"Storage directory : "
        f"{VECTOR_STORE_DIR}"
    )

    print(
        f"Collection        : "
        f"{COLLECTION_NAME}"
    )

    return vector_store


# ==========================================================
# Existing Collection Data
# ==========================================================

def _get_existing_documents(
    vector_store: Chroma,
) -> dict[str, dict[str, Any]]:
    """
    Read IDs, documents and metadata currently stored
    in Chroma.

    Returns:

        {
            "job-123": {
                "document": "...",
                "metadata": {...},
            }
        }
    """

    collection = (
        vector_store._collection
    )

    result = collection.get(
        include=[
            "documents",
            "metadatas",
        ]
    )

    ids = (
        result.get("ids")
        or []
    )

    documents = (
        result.get("documents")
        or []
    )

    metadatas = (
        result.get("metadatas")
        or []
    )

    existing: dict[
        str,
        dict[str, Any],
    ] = {}

    for index, vector_id in enumerate(
        ids
    ):

        document_text = ""

        metadata: dict[
            str,
            Any,
        ] = {}

        if index < len(
            documents
        ):

            document_text = (
                documents[index]
                or ""
            )

        if index < len(
            metadatas
        ):

            raw_metadata = (
                metadatas[index]
            )

            if isinstance(
                raw_metadata,
                dict,
            ):

                metadata = (
                    raw_metadata
                )

        existing[
            str(vector_id)
        ] = {
            "document": (
                document_text
            ),
            "metadata": metadata,
        }

    return existing


# ==========================================================
# Document Comparison
# ==========================================================

def _document_changed(
    *,
    current_document: Document,
    existing_document: dict[str, Any],
) -> bool:
    """
    Determine whether a database job differs from its
    currently indexed representation.

    Both page content and prepared metadata are compared.

    If either changed, the job must be re-embedded/upserted.
    """

    existing_text = str(
        existing_document.get(
            "document",
            "",
        )
        or ""
    )

    if (
        current_document.page_content
        != existing_text
    ):
        return True


    existing_metadata = (
        existing_document.get(
            "metadata"
        )
        or {}
    )

    if not isinstance(
        existing_metadata,
        dict,
    ):
        return True


    if (
        current_document.metadata
        != existing_metadata
    ):
        return True

    return False


# ==========================================================
# Incremental Synchronization
# ==========================================================

def sync_vector_store(
    *,
    delete_stale: bool = True,
) -> VectorSyncResult:
    """
    Synchronize Chroma with the current PostgreSQL job
    documents.

    New jobs:
        embedded and inserted.

    Changed jobs:
        re-embedded and updated.

    Unchanged jobs:
        left untouched.

    Jobs no longer present in PostgreSQL:
        removed when delete_stale=True.

    This avoids recomputing embeddings for every job during
    routine refreshes.
    """

    print()

    print(
        "Starting vector-store "
        "synchronization..."
    )


    # ------------------------------------------------------
    # Database Documents
    # ------------------------------------------------------

    job_documents = (
        build_job_documents(
            limit=None
        )
    )

    if not job_documents:

        raise RuntimeError(
            "No job documents were found "
            "in the database."
        )


    # ------------------------------------------------------
    # Current Vector Store
    # ------------------------------------------------------

    vector_store = (
        get_vector_store()
    )

    existing = (
        _get_existing_documents(
            vector_store
        )
    )


    # ------------------------------------------------------
    # Determine Required Changes
    # ------------------------------------------------------

    documents_to_add: list[
        Document
    ] = []

    ids_to_add: list[str] = []

    documents_to_update: list[
        Document
    ] = []

    ids_to_update: list[str] = []

    database_ids: set[str] = set()

    unchanged = 0


    for job_document in job_documents:

        vector_id = (
            _get_vector_id(
                job_document
            )
        )

        database_ids.add(
            vector_id
        )

        document = (
            to_langchain_document(
                job_document
            )
        )

        existing_document = (
            existing.get(
                vector_id
            )
        )


        # --------------------------------------------------
        # New Document
        # --------------------------------------------------

        if existing_document is None:

            ids_to_add.append(
                vector_id
            )

            documents_to_add.append(
                document
            )

            continue


        # --------------------------------------------------
        # Changed Document
        # --------------------------------------------------

        if _document_changed(
            current_document=document,
            existing_document=(
                existing_document
            ),
        ):

            ids_to_update.append(
                vector_id
            )

            documents_to_update.append(
                document
            )

        else:

            unchanged += 1


    # ------------------------------------------------------
    # Add New Documents
    # ------------------------------------------------------

    if documents_to_add:

        print(
            f"Adding "
            f"{len(documents_to_add)} "
            f"new vector documents..."
        )

        vector_store.add_documents(
            documents=(
                documents_to_add
            ),
            ids=ids_to_add,
        )


    # ------------------------------------------------------
    # Update Changed Documents
    # ------------------------------------------------------

    if documents_to_update:

        print(
            f"Updating "
            f"{len(documents_to_update)} "
            f"changed vector documents..."
        )

        vector_store.update_documents(
            ids=ids_to_update,
            documents=(
                documents_to_update
            ),
        )


    # ------------------------------------------------------
    # Delete Stale Documents
    # ------------------------------------------------------

    stale_ids: list[str] = []

    if delete_stale:

        existing_ids = set(
            existing.keys()
        )

        stale_ids = sorted(
            existing_ids
            - database_ids
        )

        if stale_ids:

            print(
                f"Deleting "
                f"{len(stale_ids)} "
                f"stale vector documents..."
            )

            vector_store.delete(
                ids=stale_ids
            )


    # ------------------------------------------------------
    # Final Count
    # ------------------------------------------------------

    final_collection = (
        vector_store._collection
    )

    total_indexed = (
        final_collection.count()
    )


    result = VectorSyncResult(
        database_documents=(
            len(job_documents)
        ),

        added=len(
            documents_to_add
        ),

        updated=len(
            documents_to_update
        ),

        unchanged=unchanged,

        deleted=len(
            stale_ids
        ),

        total_indexed=(
            total_indexed
        ),

        mode="incremental",
    )


    # ------------------------------------------------------
    # Report
    # ------------------------------------------------------

    print()

    print(
        "=" * 70
    )

    print(
        "VECTOR STORE SYNCHRONIZATION"
    )

    print(
        "=" * 70
    )

    print(
        f"Database documents : "
        f"{result.database_documents}"
    )

    print(
        f"Added              : "
        f"{result.added}"
    )

    print(
        f"Updated            : "
        f"{result.updated}"
    )

    print(
        f"Unchanged          : "
        f"{result.unchanged}"
    )

    print(
        f"Deleted            : "
        f"{result.deleted}"
    )

    print(
        f"Total indexed      : "
        f"{result.total_indexed}"
    )

    print(
        "=" * 70
    )

    return result


# ==========================================================
# Development / Manual Entry Point
# ==========================================================

if __name__ == "__main__":

    result = (
        sync_vector_store()
    )

    print()

    print(
        result.to_dict()
    )
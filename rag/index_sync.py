from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass
from typing import Any

from rag.document_builder import (
    JobDocument,
    build_job_documents,
)
from rag.vector_store import (
    COLLECTION_NAME,
    get_vector_store,
    to_langchain_document,
)


# ==========================================================
# Sync Result
# ==========================================================

@dataclass
class IndexSyncResult:
    """
    Summary of one database -> Chroma synchronization.
    """

    database_jobs: int
    indexed_before: int

    added: int
    updated: int
    unchanged: int
    deleted: int

    indexed_after: int

    collection: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ==========================================================
# RAG Index Synchronizer
# ==========================================================

class RAGIndexSynchronizer:
    """
    Incrementally synchronize the relational job database
    with the persistent Chroma vector index.

    Database is the source of truth.

    Stable vector ID:

        job-{job_id}

    Documents are compared using a deterministic SHA-256
    fingerprint generated from the exact text + metadata
    representation that is sent to Chroma.

    Therefore:

        new document       -> ADD
        changed document   -> UPDATE / re-embed
        unchanged document -> SKIP
        missing DB job     -> DELETE
    """

    VERSION = "rag-index-sync-v2"

    HASH_FIELD = "_document_hash"


    # ======================================================
    # Public API
    # ======================================================

    def sync(
        self,
        *,
        remove_deleted: bool = True,
    ) -> IndexSyncResult:

        print(
            "\nSynchronizing RAG vector index..."
        )

        # --------------------------------------------------
        # 1. Build current database documents
        # --------------------------------------------------

        job_documents = build_job_documents(
            limit=None
        )

        database_jobs = len(
            job_documents
        )

        print(
            f"Database documents : "
            f"{database_jobs}"
        )


        # --------------------------------------------------
        # 2. Open persistent Chroma store
        # --------------------------------------------------

        vector_store = (
            get_vector_store()
        )

        collection = (
            vector_store._collection
        )


        # --------------------------------------------------
        # 3. Read current Chroma documents
        # --------------------------------------------------

        existing_payload = (
            collection.get(
                include=[
                    "documents",
                    "metadatas",
                ]
            )
        )

        existing_ids = (
            existing_payload.get(
                "ids",
                []
            )
            or []
        )

        existing_documents = (
            existing_payload.get(
                "documents",
                []
            )
            or []
        )

        existing_metadatas = (
            existing_payload.get(
                "metadatas",
                []
            )
            or []
        )


        indexed_before = len(
            existing_ids
        )

        print(
            f"Indexed before     : "
            f"{indexed_before}"
        )


        # --------------------------------------------------
        # 4. Build existing Chroma lookup
        # --------------------------------------------------

        existing_lookup: dict[
            str,
            dict[str, Any],
        ] = {}


        for index, vector_id in enumerate(
            existing_ids
        ):

            document_text = ""

            metadata: dict[str, Any] = {}


            if index < len(
                existing_documents
            ):

                document_text = (
                    existing_documents[index]
                    or ""
                )


            if index < len(
                existing_metadatas
            ):

                raw_metadata = (
                    existing_metadatas[index]
                )

                if isinstance(
                    raw_metadata,
                    dict,
                ):

                    metadata = dict(
                        raw_metadata
                    )


            existing_lookup[
                str(vector_id)
            ] = {
                "document": document_text,
                "metadata": metadata,
            }


        existing_id_set = set(
            existing_lookup.keys()
        )


        # --------------------------------------------------
        # 5. Build current database lookup
        # --------------------------------------------------

        current_lookup: dict[
            str,
            dict[str, Any],
        ] = {}


        for job_document in job_documents:

            raw_job_id = (
                job_document
                .metadata
                .get("job_id")
            )


            if raw_job_id is None:

                print(
                    "Skipping document "
                    "without job_id."
                )

                continue


            vector_id = (
                f"job-{raw_job_id}"
            )


            langchain_document = (
                to_langchain_document(
                    job_document
                )
            )


            document_hash = (
                self._fingerprint(
                    text=(
                        langchain_document
                        .page_content
                    ),
                    metadata=(
                        langchain_document
                        .metadata
                    ),
                )
            )


            # Store the fingerprint in Chroma metadata.
            # This makes future syncs cheap because we can
            # compare hashes without comparing all fields.
            langchain_document.metadata[
                self.HASH_FIELD
            ] = document_hash


            current_lookup[
                vector_id
            ] = {
                "document": langchain_document,
                "hash": document_hash,
            }


        current_ids = set(
            current_lookup.keys()
        )


        # --------------------------------------------------
        # 6. Determine new / deleted IDs
        # --------------------------------------------------

        new_ids = (
            current_ids
            - existing_id_set
        )


        deleted_ids = (
            existing_id_set
            - current_ids
        )


        common_ids = (
            current_ids
            & existing_id_set
        )


        # --------------------------------------------------
        # 7. Determine changed / unchanged IDs
        # --------------------------------------------------

        changed_ids: set[str] = set()

        unchanged_ids: set[str] = set()


        for vector_id in common_ids:

            current_hash = (
                current_lookup[
                    vector_id
                ]["hash"]
            )


            existing_entry = (
                existing_lookup[
                    vector_id
                ]
            )


            existing_metadata = (
                existing_entry[
                    "metadata"
                ]
            )


            stored_hash = (
                existing_metadata.get(
                    self.HASH_FIELD
                )
            )


            # ----------------------------------------------
            # New v2 indexes contain _document_hash.
            # ----------------------------------------------

            if stored_hash:

                if (
                    str(stored_hash)
                    == current_hash
                ):

                    unchanged_ids.add(
                        vector_id
                    )

                else:

                    changed_ids.add(
                        vector_id
                    )

                continue


            # ----------------------------------------------
            # Migration from the old vector index.
            #
            # Existing v1 documents have no hash. Compare
            # their current stored text/metadata directly.
            # ----------------------------------------------

            existing_hash = (
                self._fingerprint(
                    text=(
                        existing_entry[
                            "document"
                        ]
                    ),
                    metadata=(
                        existing_metadata
                    ),
                )
            )


            if (
                existing_hash
                == current_hash
            ):

                # Content is unchanged, but the old document
                # does not yet contain _document_hash.
                #
                # Mark it changed once so its metadata gets
                # migrated to the v2 format.
                changed_ids.add(
                    vector_id
                )

            else:

                changed_ids.add(
                    vector_id
                )


        # --------------------------------------------------
        # 8. Add new jobs
        # --------------------------------------------------

        added = 0


        if new_ids:

            ordered_new_ids = (
                self._sort_ids(
                    new_ids
                )
            )


            new_documents = [
                current_lookup[
                    vector_id
                ]["document"]

                for vector_id
                in ordered_new_ids
            ]


            vector_store.add_documents(
                documents=new_documents,
                ids=ordered_new_ids,
            )


            added = len(
                ordered_new_ids
            )


        # --------------------------------------------------
        # 9. Update changed jobs only
        # --------------------------------------------------

        updated = 0


        if changed_ids:

            ordered_changed_ids = (
                self._sort_ids(
                    changed_ids
                )
            )


            changed_documents = [
                current_lookup[
                    vector_id
                ]["document"]

                for vector_id
                in ordered_changed_ids
            ]


            vector_store.update_documents(
                ids=ordered_changed_ids,
                documents=changed_documents,
            )


            updated = len(
                ordered_changed_ids
            )


        # --------------------------------------------------
        # 10. Delete stale jobs
        # --------------------------------------------------

        deleted = 0


        if (
            remove_deleted
            and deleted_ids
        ):

            ordered_deleted_ids = (
                self._sort_ids(
                    deleted_ids
                )
            )


            vector_store.delete(
                ids=ordered_deleted_ids
            )


            deleted = len(
                ordered_deleted_ids
            )


        # --------------------------------------------------
        # 11. Final index count
        # --------------------------------------------------

        indexed_after = (
            collection.count()
        )


        unchanged = len(
            unchanged_ids
        )


        # --------------------------------------------------
        # 12. Build result
        # --------------------------------------------------

        result = IndexSyncResult(

            database_jobs=database_jobs,

            indexed_before=indexed_before,

            added=added,

            updated=updated,

            unchanged=unchanged,

            deleted=deleted,

            indexed_after=indexed_after,

            collection=COLLECTION_NAME,
        )


        # --------------------------------------------------
        # 13. Summary
        # --------------------------------------------------

        print(
            "\nRAG index synchronization complete."
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
            f"Indexed after      : "
            f"{result.indexed_after}"
        )

        print(
            f"Collection         : "
            f"{result.collection}"
        )


        return result


    # ======================================================
    # Fingerprint
    # ======================================================

    @classmethod
    def _fingerprint(
        cls,
        *,
        text: str,
        metadata: dict[str, Any],
    ) -> str:
        """
        Produce a deterministic fingerprint from the exact
        text and metadata representation stored in Chroma.

        Internal synchronization metadata such as
        _document_hash is excluded.
        """

        cleaned_metadata = {
            str(key): cls._normalize_value(
                value
            )

            for key, value
            in metadata.items()

            if key != cls.HASH_FIELD
        }


        metadata_parts = [

            f"{key}={cleaned_metadata[key]}"

            for key in sorted(
                cleaned_metadata
            )
        ]


        payload = (
            str(text)
            + "\n\n---METADATA---\n"
            + "\n".join(
                metadata_parts
            )
        )


        return (
            hashlib.sha256(
                payload.encode(
                    "utf-8"
                )
            )
            .hexdigest()
        )


    # ======================================================
    # Metadata Normalization
    # ======================================================

    @staticmethod
    def _normalize_value(
        value: Any,
    ) -> str:

        if value is None:
            return ""

        if isinstance(
            value,
            bool,
        ):

            return (
                "true"
                if value
                else "false"
            )

        return str(
            value
        ).strip()


    # ======================================================
    # Stable ID Ordering
    # ======================================================

    @staticmethod
    def _sort_ids(
        ids: set[str],
    ) -> list[str]:
        """
        Sort job IDs numerically where possible.

        Example:

            job-2
            job-10

        rather than lexicographically:

            job-10
            job-2
        """

        def sort_key(
            vector_id: str,
        ) -> tuple[int, str]:

            prefix = "job-"


            if vector_id.startswith(
                prefix
            ):

                suffix = (
                    vector_id[
                        len(prefix):
                    ]
                )


                try:

                    return (
                        int(suffix),
                        vector_id,
                    )

                except ValueError:
                    pass


            return (
                10**18,
                vector_id,
            )


        return sorted(
            ids,
            key=sort_key,
        )


# ==========================================================
# Convenience Function
# ==========================================================

def sync_vector_store(
    remove_deleted: bool = True,
) -> IndexSyncResult:
    """
    Incrementally synchronize database jobs with Chroma.
    """

    synchronizer = (
        RAGIndexSynchronizer()
    )


    return synchronizer.sync(
        remove_deleted=remove_deleted
    )


# ==========================================================
# CLI
# ==========================================================

if __name__ == "__main__":

    result = (
        sync_vector_store()
    )


    print(
        "\nSync summary:"
    )

    print(
        result.to_dict()
    )
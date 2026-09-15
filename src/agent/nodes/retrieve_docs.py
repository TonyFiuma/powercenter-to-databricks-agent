from src.agent.state import AgentState

from src.rag.query_builder import (
    extract_transformation_types,
    build_powercenter_retrieval_query,
    build_databricks_retrieval_query,
)

from src.rag.retriever import (
    load_vectorstore,
    retrieve_documents,
)

from src.rag.databricks_retriever import (
    load_databricks_vectorstore,
    retrieve_databricks_documents,
)


def retrieve_docs_node(
    state: AgentState,
) -> dict:
    """
    Retrieve PowerCenter and Databricks documentation
    for each transformation found in the parsed mapping.

    PowerCenter retrieval is version-aware.

    Vector stores are loaded lazily so that the RAG
    infrastructure is initialized only when this node
    is actually executed.
    """

    mapping = state["mapping"]

    powercenter_version = state.get(
        "powercenter_version"
    )

    if not powercenter_version:
        raise ValueError(
            "PowerCenter version not found "
            "in agent state."
        )

    # --------------------------------------------------
    # Lazy RAG initialization
    # --------------------------------------------------

    print(
        "\nInitializing RAG vector stores."
    )

    powercenter_vectorstore = (
        load_vectorstore()
    )

    databricks_vectorstore = (
        load_databricks_vectorstore()
    )

    mapplets = state.get(
    "mapplets",
    [],
)

    transformation_types = (
        extract_transformation_types(
            mapping=mapping,
            mapplets=mapplets,
        )
    )

    print(
        f"Transformation types found: "
        f"{transformation_types}"
    )

    print(
        f"PowerCenter documentation version: "
        f"{powercenter_version}"
    )

    all_docs = []
    retrieval_queries = []

    # Metadata filter used only for
    # PowerCenter documentation.
    retrieval_filters = {
        "$and": [
            {
                "product": {
                    "$eq": "powercenter"
                }
            },
            {
                "version": {
                    "$eq": powercenter_version
                }
            },
        ]
    }

    for transformation_type in transformation_types:

        # ----------------------------------------------
        # Build retrieval queries
        # ----------------------------------------------

        powercenter_query = (
            build_powercenter_retrieval_query(
                transformation_type
            )
        )

        databricks_query = (
            build_databricks_retrieval_query(
                transformation_type
            )
        )

        retrieval_queries.append(
            f"PowerCenter: {powercenter_query}"
        )

        retrieval_queries.append(
            f"Databricks: {databricks_query}"
        )

        print(
            f"\nRetrieving documentation for: "
            f"{transformation_type}"
        )

        # ----------------------------------------------
        # PowerCenter retrieval
        # ----------------------------------------------

        print(
            f"PowerCenter query: "
            f"{powercenter_query}"
        )

        print(
            f"PowerCenter filters: "
            f"{retrieval_filters}"
        )

        powercenter_docs = (
            retrieve_documents(
                vectorstore=powercenter_vectorstore,
                query=powercenter_query,
                k=1,
                filters=retrieval_filters,
            )
        )

        # ----------------------------------------------
        # Databricks retrieval
        # ----------------------------------------------

        print(
            f"Databricks query: "
            f"{databricks_query}"
        )

        databricks_docs = (
            retrieve_databricks_documents(
                vectorstore=databricks_vectorstore,
                query=databricks_query,
                k=1,
            )
        )

        # ----------------------------------------------
        # Collect retrieved documents
        # ----------------------------------------------

        all_docs.extend(
            powercenter_docs
        )

        all_docs.extend(
            databricks_docs
        )

    return {
        "retrieval_query": "\n".join(
            retrieval_queries
        ),
        "retrieval_filters": (
            retrieval_filters
        ),
        "retrieved_docs": all_docs,
    }
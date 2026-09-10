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


powercenter_vectorstore = load_vectorstore()
databricks_vectorstore = load_databricks_vectorstore()


def retrieve_docs_node(state: AgentState) -> dict:
    """
    Retrieve PowerCenter and Databricks documentation
    for each transformation found in the parsed mapping.
    """

    mapping = state["mapping"]

    transformation_types = extract_transformation_types(
        mapping
    )

    print(
        f"Transformation types found: "
        f"{transformation_types}"
    )

    all_docs = []
    retrieval_queries = []

    for transformation_type in transformation_types:

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

        print(
            f"PowerCenter query: "
            f"{powercenter_query}"
        )

        powercenter_docs = retrieve_documents(
            vectorstore=powercenter_vectorstore,
            query=powercenter_query,
            k=1,
        )

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
        "retrieved_docs": all_docs,
    }

from pathlib import Path

from agent1.agent import MigrationKnowledgeAgent


def main():

    print("\n===== INITIALIZING AGENT 1 =====")

    agent = MigrationKnowledgeAgent()

    print("Agent 1 initialized successfully.")

    # --------------------------------
    # INGEST DOCUMENT
    # --------------------------------

    document_path = "documents/migration_docs/langchain_langgraph_migration_guide.pdf"

    print("\n===== DOCUMENT INGESTION =====")

    if not Path(document_path).exists():
        raise FileNotFoundError(
            f"Migration document not found: {document_path}"
        )

    result = agent.ingest_document(document_path)

    print("Ingestion completed.")

    print("Chunks added:", result["chunks_added"])
    print("Rules extracted:", result["rules_added"])

    # --------------------------------
    # CHECK STORED RULES
    # --------------------------------

    print("\n===== EXTRACTED MIGRATION RULES =====")

    rules = agent.get_rules()

    print("Total rules:", len(rules))

    for index, rule in enumerate(rules[:5], start=1):
        print(f"\nRule {index}:")
        print(rule)

    # --------------------------------
    # TEST RETRIEVAL
    # --------------------------------

    print("\n===== TEST DOCUMENT RETRIEVAL =====")

    query = "LangChain import migration rules"

    results = agent.search(query)

    print("Retrieved chunks:", len(results))

    for result in results:

        print("\nChunk ID:", result["chunk_id"])
        print("Similarity:", result["score"])
        print("Source:", result["source"])
        print("Text:", result["text"][:300])

    # --------------------------------
    # CHECK SAVED FILES
    # --------------------------------

    print("\n===== CHECK STORAGE FILES =====")

    files = [
        "vector_store/index.faiss",
        "vector_store/metadata.json",
        "vector_store/rules.json"
    ]

    for file in files:

        print(
            file,
            "EXISTS" if Path(file).exists() else "MISSING"
        )


if __name__ == "__main__":
    main()

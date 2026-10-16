from agent1.agent import MigrationKnowledgeAgent


def main():

    agent = MigrationKnowledgeAgent.__new__(
        MigrationKnowledgeAgent
    )

    # Initialize the components without requiring
    # an existing FAISS index.
    from agent1.embeddings import EmbeddingModel
    from agent1.vector_store import VectorStore
    from agent1.metadata_store import MetadataStore

    agent.vector_index = "vector_store/index.faiss"
    agent.metadata_file = "vector_store/metadata.json"

    agent.embedding_model = EmbeddingModel()

    agent.vector_store = VectorStore(dimension=384)

    agent.metadata_store = MetadataStore()

    print("\nBuilding migration knowledge index...")

    count = agent.ingest_directory(
        "documents/migration_docs"
    )

    print("\n" + "=" * 70)
    print("INDEX BUILD COMPLETE")
    print("=" * 70)

    print(f"Total chunks: {count}")
    print("FAISS index: vector_store/index.faiss")
    print("Metadata: vector_store/metadata.json")


if __name__ == "__main__":
    main()
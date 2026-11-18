
from agent1.agent import MigrationKnowledgeAgent


def main():

    print("===== LOADING SAVED AGENT 1 DATA =====")

    agent = MigrationKnowledgeAgent()
    print("\n===== STORAGE DEBUG =====")

    print("Vector count:", agent.vector_store.size())
    print("Metadata count:", len(agent.metadata_store.chunks))
    print("Similarity threshold:", agent.retriever.similarity_threshold)

    print("First metadata chunk:")
    print(agent.metadata_store.get(0))
    print("Agent initialized successfully.")
    print("\n===== RAW SIMILARITY SCORES =====")

    query = "How should ChatOpenAI imports be migrated?"

    query_embedding = agent.embedding_model.embed_query(query)

    scores, indices = agent.vector_store.search(
        query_embedding,
        top_k=10
    )

    for score, index in zip(scores, indices):
        print(f"Index: {index}, Similarity: {score:.4f}")
    # Test saved rules
    rules = agent.get_rules()

    print("\n===== SAVED RULES =====")
    print("Total rules:", len(rules))

    for rule in rules[:3]:
        print(rule)

    # Test retrieval
    print("\n===== SAVED VECTOR RETRIEVAL =====")

    results = agent.search(
        "How should ChatOpenAI imports be migrated?"
    )

    print("Retrieved chunks:", len(results))

    for result in results:
        print("\nChunk:", result["chunk_id"])
        print("Score:", result["score"])
        print("Text:", result["text"][:200])


if __name__ == "__main__":
    main()

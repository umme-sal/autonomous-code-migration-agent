from agent1.agent import MigrationKnowledgeAgent


agent = MigrationKnowledgeAgent()


query = "How does middleware control agent execution?"

results = agent.search(query)


print("\n" + "=" * 60)
print("MIGRATION KNOWLEDGE")
print("=" * 60)


if not results:

    print("No relevant information found.")

else:

    for rank, result in enumerate(results, start=1):

        print(f"\nRank {rank}")
        print(f"Score: {result['score']:.4f}")
        print(f"Chunk ID: {result['chunk_id']}")
        print(f"Source: {result['source']}")

        print("\nText:")
        print(result["text"])
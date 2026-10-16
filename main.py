from agent2.agent import CodeMigrationAgent


def main():

    source_code = """
from old_library import OldClass


class MyClass:

    def hello(self):

        obj = OldClass()

        return obj


def create_object():

    return OldClass()
"""

    print("\n" + "=" * 70)
    print("AUTONOMOUS CODE MIGRATION AGENT")
    print("AGENT 2 → AGENT 1 CONNECTION")
    print("=" * 70)

    print("\nSOURCE CODE:")
    print("-" * 70)
    print(source_code)

    # Create Agent 2
    agent = CodeMigrationAgent()

    # Agent 2 analyzes the source code
    analyzer = agent.analyze(source_code)

    print("\n" + "=" * 70)
    print("AGENT 2 - MIGRATION CANDIDATES")
    print("=" * 70)

    for candidate in analyzer.migration_candidates:

        print("\nType:")
        print(candidate["type"])

        print("Code:")
        print(candidate["code"])

    # Agent 2 calls Agent 1
    print("\n" + "=" * 70)
    print("AGENT 2 → AGENT 1")
    print("=" * 70)

    knowledge = agent.retrieve_knowledge(source_code)

    # Display retrieved knowledge
    print("\n" + "=" * 70)
    print("AGENT 1 - RETRIEVED MIGRATION KNOWLEDGE")
    print("=" * 70)

    for item in knowledge:

        candidate = item["candidate"]
        results = item["results"]

        print("\nMigration Candidate:")
        print(candidate["code"])

        if not results:
            print("\nNo relevant knowledge found.")
            continue

        for rank, result in enumerate(results, start=1):

            print(f"\nResult {rank}")
            print(f"Similarity Score : {result['score']:.4f}")
            print(f"Chunk ID          : {result['chunk_id']}")
            print(f"Source            : {result['source']}")

            print("\nRetrieved Text:")
            print(result["text"])

    print("\n" + "=" * 70)
    print("END OF AGENT 2 → AGENT 1 DEMONSTRATION")
    print("=" * 70)


if __name__ == "__main__":
    main()
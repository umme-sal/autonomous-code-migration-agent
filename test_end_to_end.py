from agent2.agent import CodeMigrationAgent


def main():

    source_code = """
from langchain.chat_models import ChatOpenAI

llm = ChatOpenAI()

print("ChatOpenAI should be migrated")
"""

    print("\n" + "=" * 70)
    print("ORIGINAL SOURCE CODE")
    print("=" * 70)

    print(source_code)

    # ---------------------------------------------
    # Create Agent 2
    # ---------------------------------------------

    agent = CodeMigrationAgent()

    # ---------------------------------------------
    # Run complete migration
    # ---------------------------------------------

    migrated_code = agent.migrate_code(
        source_code
    )

    # ---------------------------------------------
    # Display result
    # ---------------------------------------------

    print("\n" + "=" * 70)
    print("FINAL MIGRATED CODE")
    print("=" * 70)

    print(migrated_code)


if __name__ == "__main__":
    main()
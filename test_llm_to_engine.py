from agent2.migration_engine import MigrationEngine


def main():

    source_code = """
from langchain.chat_models import ChatOpenAI

llm = ChatOpenAI()

print("ChatOpenAI should be migrated")
"""

    migration_map = {
        "langchain.chat_models": {
            "module": "langchain_openai",
            "names": {
                "ChatOpenAI": "ChatOpenAI"
            }
        }
    }

    engine = MigrationEngine()

    migrated_code = engine.migrate(
        source_code,
        migration_map
    )

    print("\n" + "=" * 70)
    print("ORIGINAL")
    print("=" * 70)

    print(source_code)

    print("\n" + "=" * 70)
    print("MIGRATED")
    print("=" * 70)

    print(migrated_code)


if __name__ == "__main__":
    main()
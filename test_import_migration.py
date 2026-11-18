
from agent2.migration_engine import MigrationEngine


def main():

    source_code = """
from langchain.chat_models import ChatOpenAI

llm = ChatOpenAI()
"""

    migration_map = {
        "langchain.chat_models": "langchain_openai"
    }

    print("===== ORIGINAL CODE =====")
    print(source_code)

    engine = MigrationEngine()

    migrated_code = engine.migrate(
        source_code,
        migration_map
    )

    print("\n===== MIGRATED CODE =====")
    print(migrated_code)


if __name__ == "__main__":
    main()

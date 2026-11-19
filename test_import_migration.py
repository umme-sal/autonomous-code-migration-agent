
from agent2.migration_engine import MigrationEngine


def main():

    source_code = """
from langchain.chat_models import ChatOpenAI

llm = ChatOpenAI()
"""

    migration_rules = [
        {
            "type": "symbol",
            "source": "ChatOpenAI",
            "target": "ChatOpenAI",
            "source_module": "langchain.chat_models",
            "target_module": "langchain_openai"
        }
    ]

    print("===== ORIGINAL CODE =====")
    print(source_code)

    print("\n===== MIGRATION RULES =====")
    print(migration_rules)

    engine = MigrationEngine()

    migrated_code = engine.migrate(
        source_code,
        migration_rules
    )

    print("\n===== MIGRATED CODE =====")
    print(migrated_code)

    expected_import = "from langchain_openai import ChatOpenAI"

    assert expected_import in migrated_code

    print("\nTEST PASSED!")


if __name__ == "__main__":
    main()

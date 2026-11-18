
from agent1.agent import MigrationKnowledgeAgent
from agent2.migration_planner import MigrationPlanner
from agent2.migration_engine import MigrationEngine


def migrate_code(source_code: str):

    print("\n===== INITIALIZING AGENT 1 =====")

    agent1 = MigrationKnowledgeAgent()

    print("Agent 1 initialized.")

    print("\n===== LOADING MIGRATION RULES =====")

    migration_rules = agent1.get_rules()

    print("Rules available:", len(migration_rules))

    print("\n===== RETRIEVING DOCUMENTATION =====")

    retrieved_docs = agent1.search(
        "LangChain Python migration rules import and API changes"
    )

    print("Retrieved chunks:", len(retrieved_docs))

    print("\n===== INITIALIZING MIGRATION PLANNER =====")

    planner = MigrationPlanner()

    print("Migration Planner initialized.")

    print("\n===== GENERATING EDIT PLAN =====")

    edit_plan = planner.generate_edit_plan(
        source_code=source_code,
        retrieved_docs=retrieved_docs,
        migration_rules=migration_rules
    )

    print("Generated edit plan:")
    print(edit_plan)

    print("\n===== INITIALIZING MIGRATION ENGINE =====")

    engine = MigrationEngine()

    # Step 1: Apply deterministic import and symbol migrations.
    migrated_code = engine.migrate(
        source_code,
        migration_rules
    )

    print("\n===== IMPORT AND SYMBOL MIGRATION COMPLETED =====")

    # Step 2: Apply LLM-generated function-call edits.
    final_code = engine.migrate_with_edit_plan(
        migrated_code,
        edit_plan
    )

    print("\n===== FINAL MIGRATED CODE =====")

    print(final_code)

    return final_code


def main():

    source_code = """
from langchain.chat_models import ChatOpenAI

llm = ChatOpenAI()
"""

    print("===== ORIGINAL SOURCE CODE =====")
    print(source_code)

    migrate_code(source_code)


if __name__ == "__main__":
    main()

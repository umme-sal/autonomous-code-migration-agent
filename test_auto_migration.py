
from agent1.agent import MigrationKnowledgeAgent
from agent2.migration_engine import MigrationEngine


def main():

    print("\n===== INITIALIZING AGENT 1 =====")

    agent1 = MigrationKnowledgeAgent()

    print("Agent 1 initialized.")

    migration_rules = agent1.get_rules()

    print("\n===== EXTRACTED RULES =====")
    print("Total rules:", len(migration_rules))

    engine = MigrationEngine()

    migration_map = engine.build_migration_map(
        migration_rules
    )

    print("\n===== AUTOMATICALLY GENERATED MIGRATION MAP =====")

    for old_module, new_module in migration_map.items():
        print(f"{old_module} -> {new_module}")

    source_code = """
from langchain.agents import initialize_agent

agent = initialize_agent()
"""

    print("\n===== ORIGINAL CODE =====")
    print(source_code)

    migrated_code = engine.migrate(
        source_code,
        migration_rules
    )

    print("\n===== MIGRATED CODE =====")
    print(migrated_code)


if __name__ == "__main__":
    main()

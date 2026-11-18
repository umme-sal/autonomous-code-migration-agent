
from agent1.agent import MigrationKnowledgeAgent
from agent2.migration_planner import MigrationPlanner
from agent2.edit_plan_validator import EditPlanValidator


def main():

    print("\n===== INITIALIZING AGENT 1 =====")

    agent1 = MigrationKnowledgeAgent()

    print("Agent 1 initialized.")

    print("\n===== INITIALIZING MIGRATION PLANNER =====")

    planner = MigrationPlanner()

    print("Migration Planner initialized.")

    # Example legacy Python code
    source_code = """
def ask_model(prompt):
    result = client.invoke(prompt)
    return result
"""

    print("\n===== SOURCE CODE =====")
    print(source_code)

    # Retrieve relevant documentation
    print("\n===== RETRIEVING DOCUMENTATION =====")

    retrieved_docs = agent1.search(
    "ChatOpenAI import migration from langchain.chat_models to langchain_openai"
)
    print("Retrieved chunks:", len(retrieved_docs))

    # Get extracted migration rules
    migration_rules = agent1.get_rules()

    print("\n===== ALL EXTRACTED RULES =====")

    for index, rule in enumerate(migration_rules, start=1):
        print(f"\nRule {index}:")
        print(rule)

    # Generate edit plan
    print("\n===== GENERATING EDIT PLAN =====")

    edit_plan = planner.generate_edit_plan(
        source_code=source_code,
        retrieved_docs=retrieved_docs,
        migration_rules=migration_rules
    )

    print("\nGenerated Edit Plan:")
    print(edit_plan)

    # Validate generated plan
    print("\n===== VALIDATING EDIT PLAN =====")

    validator = EditPlanValidator()

    validation_result = validator.validate(
        source_code,
        edit_plan
    )

    print(validation_result)


if __name__ == "__main__":
    main()

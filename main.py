
from agent1.agent import MigrationKnowledgeAgent
from agent2.code_analyzer import CodeAnalyzer
from agent2.migration_planner import MigrationPlanner
from agent2.migration_engine import MigrationEngine
import libcst as cst

def generate_retrieval_queries(candidates: list[dict]) -> list[str]:

    queries = []

    for candidate in candidates:

        if candidate["type"] != "import":
            continue

        rule = candidate["rule"]

        query = (
            f"Migrate {rule['source']} "
            f"from {rule['source_module']} "
            f"to {rule['target_module']}. "
            f"Find migration instructions and examples."
        )

        if query not in queries:
            queries.append(query)

    return queries


def retrieve_relevant_documentation(
    agent1,
    queries: list[str]
) -> list[dict]:

    retrieved_docs = []
    seen_chunks = set()

    for query in queries:

        print(f"\nRetrieval query: {query}")

        results = agent1.search(query)

        for result in results:

            chunk_id = result["chunk_id"]

            if chunk_id not in seen_chunks:
                seen_chunks.add(chunk_id)
                retrieved_docs.append(result)

    return retrieved_docs


def migrate_code(source_code: str):

    print("\n===== INITIALIZING AGENT 1 =====")

    agent1 = MigrationKnowledgeAgent()

    print("Agent 1 initialized.")

    migration_rules = agent1.get_rules()

    print("\nRules available:", len(migration_rules))

    # --------------------------------------------------
    # STEP 1: DYNAMIC CST CANDIDATE DETECTION
    # --------------------------------------------------

    print("\n===== ANALYZING SOURCE CODE =====")

    analyzer = CodeAnalyzer(migration_rules)


    module = cst.parse_module(source_code)
    module.visit(analyzer)

    candidates = analyzer.migration_candidates

    print("\nDetected migration candidates:")

    for candidate in candidates:
        print(candidate)

    # --------------------------------------------------
    # STEP 2: GENERATE DYNAMIC RETRIEVAL QUERIES
    # --------------------------------------------------

    print("\n===== GENERATING RETRIEVAL QUERIES =====")

    queries = generate_retrieval_queries(candidates)

    if not queries:
        print("No matching migration rules found.")

    # --------------------------------------------------
    # STEP 3: RETRIEVE RELEVANT DOCUMENTATION
    # --------------------------------------------------

    print("\n===== RETRIEVING DOCUMENTATION =====")

    retrieved_docs = retrieve_relevant_documentation(
        agent1,
        queries
    )

    print("\nTotal retrieved chunks:", len(retrieved_docs))

    # --------------------------------------------------
    # STEP 4: GENERATE EDIT PLAN
    # --------------------------------------------------

    print("\n===== INITIALIZING MIGRATION PLANNER =====")

    planner = MigrationPlanner()

    print("\n===== GENERATING EDIT PLAN =====")

    edit_plan = planner.generate_edit_plan(
        source_code=source_code,
        retrieved_docs=retrieved_docs,
        migration_rules=migration_rules
    )

    print("\nGenerated edit plan:")
    print(edit_plan)

    # --------------------------------------------------
    # STEP 5: APPLY MIGRATION
    # --------------------------------------------------

    print("\n===== INITIALIZING MIGRATION ENGINE =====")

    engine = MigrationEngine()

    migrated_code = engine.migrate(
        source_code,
        migration_rules
    )

    final_code = engine.migrate_with_edit_plan(
        migrated_code,
        edit_plan
    )

    # --------------------------------------------------
    # STEP 6: DISPLAY RESULT
    # --------------------------------------------------

    print("\n===== FINAL MIGRATED CODE =====")

    print(final_code)

    return final_code


def main():

    source_code = """
import os
import json

def calculate_sum(a, b):
    return a + b
"""

    print("===== ORIGINAL SOURCE CODE =====")
    print(source_code)

    migrate_code(source_code)


if __name__ == "__main__":
    main()

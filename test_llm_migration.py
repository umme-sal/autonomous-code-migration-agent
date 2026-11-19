
from agent1.agent import MigrationKnowledgeAgent
from agent2.migration_planner import MigrationPlanner
from agent2.migration_engine import MigrationEngine


# ==========================================
# 1. INITIALIZE AGENT 1
# ==========================================

print("\n===== INITIALIZING AGENT 1 =====")

agent1 = MigrationKnowledgeAgent()

print("Agent 1 initialized successfully.")


# ==========================================
# 2. DEFINE SOURCE CODE
# ==========================================

source_code = """
client = SomeClient()

result = client.old_method("hello")
"""

print("\n===== ORIGINAL SOURCE CODE =====")
print(source_code)


# ==========================================
# 3. RETRIEVE MIGRATION RULES
# ==========================================

print("\n===== RETRIEVING MIGRATION RULES =====")

query = "Rename deprecated method old_method to new_method"

retrieved_docs = agent1.search(query)

print(f"Retrieved documents: {len(retrieved_docs)}")

for index, doc in enumerate(retrieved_docs, start=1):
    print(f"\nDocument {index}:")
    print(doc.get("text", "")[:500])


# ==========================================
# 4. GET STRUCTURED MIGRATION RULES
# ==========================================

migration_rules = agent1.get_rules()

print("\n===== AVAILABLE MIGRATION RULES =====")
print(f"Total rules: {len(migration_rules)}")


# ==========================================
# 5. INITIALIZE LLM PLANNER
# ==========================================

print("\n===== INITIALIZING MIGRATION PLANNER =====")

planner = MigrationPlanner()

print("Migration planner initialized.")


# ==========================================
# 6. GENERATE EDIT PLAN USING GROQ
# ==========================================

print("\n===== GENERATING EDIT PLAN =====")

edit_plan = planner.generate_edit_plan(
    source_code=source_code,
    retrieved_docs=retrieved_docs,
    migration_rules=migration_rules
)

print("\n===== GENERATED EDIT PLAN =====")
print(edit_plan)


# ==========================================
# 7. APPLY MIGRATION
# ==========================================

print("\n===== APPLYING MIGRATION =====")

engine = MigrationEngine()

migrated_code = engine.migrate_with_edit_plan(
    source_code=source_code,
    edit_plan=edit_plan
)

print("\n===== MIGRATED CODE =====")
print(migrated_code)


# ==========================================
# 8. FINAL RESULT
# ==========================================

print("\n===== MIGRATION COMPLETED =====")

if migrated_code != source_code:
    print("Migration was applied.")
else:
    print("No executable migration was applied.")

if edit_plan.get("manual_review"):
    print("\nManual review required for:")
    for rule_id in edit_plan["manual_review"]:
        print("-", rule_id)

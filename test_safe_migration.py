from agent2.migration_engine import MigrationEngine

source_code = """
def ask_model(prompt):
    result = client.run(prompt)
    return result
"""

valid_plan = {
    "migration_required": True,
    "reason": "Replace deprecated run method",
    "targets": [
        {
            "target_code": "client.run(prompt)",
            "edits": [
                {
                    "target": "method_name",
                    "operation": "replace",
                    "value": {
                        "type": "identifier",
                        "name": "invoke"
                    }
                },
                {
                    "target": "arguments",
                    "operation": "replace",
                    "value": [
                        {
                            "type": "keyword_argument",
                            "name": "input",
                            "value": {
                                "type": "identifier",
                                "name": "prompt"
                            }
                        }
                    ]
                }
            ]
        }
    ]
}

engine = MigrationEngine()

# Test valid plan
print("===== VALID PLAN =====")
result = engine.migrate_with_edit_plan(source_code, valid_plan)
print(result)


# Test invalid plan
invalid_plan = valid_plan.copy()
invalid_plan["targets"] = [
    {
        "target_code": "client.delete(prompt)",
        "edits": valid_plan["targets"][0]["edits"]
    }
]

print("\n===== INVALID PLAN =====")

try:
    engine.migrate_with_edit_plan(source_code, invalid_plan)
except ValueError as e:
    print(e)

# ==========================================
# TEST 3: AMBIGUOUS TARGET SAFETY
# ==========================================

duplicate_source = """
def first():
    return client.run(prompt)

def second():
    return client.run(prompt)
"""

print("\n===== AMBIGUOUS TARGET THROUGH ENGINE =====")

try:
    result = engine.migrate_with_edit_plan(
        duplicate_source,
        valid_plan
    )
    print(result)

except ValueError as e:
    print("Migration blocked:")
    print(e)
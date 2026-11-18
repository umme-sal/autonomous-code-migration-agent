import ast

from agent2.migration_engine import MigrationEngine


source_code = """
def ask_model(prompt):
    result = client.run(prompt)
    return result
"""


edit_plan = {
    "migration_required": True,
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
                            "type": "positional_argument",
                            "value": {
                                "type": "dictionary",
                                "entries": [
                                    {
                                        "key": "input",
                                        "value": {
                                            "type": "identifier",
                                            "name": "prompt"
                                        }
                                    }
                                ]
                            }
                        },
                        {
                            "type": "keyword_argument",
                            "name": "timeout",
                            "value": {
                                "type": "number",
                                "value": 30
                            }
                        },
                        {
                            "type": "keyword_argument",
                            "name": "debug",
                            "value": {
                                "type": "boolean",
                                "value": True
                            }
                        }
                    ]
                }
            ]
        }
    ]
}


engine = MigrationEngine()

migrated_code = engine.migrate_with_edit_plan(
    source_code,
    edit_plan
)

print("\n===== MIGRATED CODE =====\n")
print(migrated_code)


# ------------------------------------------
# SYNTAX VALIDATION
# ------------------------------------------

print("\n===== SYNTAX VALIDATION =====\n")

try:
    ast.parse(migrated_code)
    print("SUCCESS: Migrated code has valid Python syntax.")

except SyntaxError as error:
    print("FAILED: Migrated code contains a syntax error.")
    print(error)
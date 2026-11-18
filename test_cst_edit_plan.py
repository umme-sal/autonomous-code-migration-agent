
from agent2.migration_engine import MigrationEngine


source_code = """
def ask_model(prompt):
    result = client.run(prompt)
    return result
"""

edit_plan = {
    "migration_required": True,
    "reason": "Replace run with invoke and pass input as a keyword argument.",
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

migrated_code = engine.migrate_with_edit_plan(
    source_code,
    edit_plan
)

print("===== ORIGINAL CODE =====")
print(source_code)

print("===== MIGRATED CODE =====")
print(migrated_code)

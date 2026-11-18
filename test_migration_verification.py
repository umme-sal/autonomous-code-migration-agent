
from agent2.migration_engine import MigrationEngine


source_code = """
def ask_model(prompt):
    result = client.invoke(prompt)
    return result
"""


edit_plan = {
    "migration_required": True,
    "targets": [
        {
            "target_code": "client.invoke(prompt)",
            "edits": [
                {
                    "target": "method_name",
                    "operation": "replace",
                    "value": {
                        "type": "identifier",
                        "name": "run"
                    }
                }
            ]
        }
    ]
}

engine = MigrationEngine()

try:

    migrated_code = engine.migrate_with_edit_plan(
        source_code,
        edit_plan
    )

    print("MIGRATED CODE:")
    print(migrated_code)

except ValueError as error:

    print("MIGRATION BLOCKED:")
    print(error)

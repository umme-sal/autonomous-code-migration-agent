
from agent2.migration_engine import MigrationEngine


engine = MigrationEngine()

source_code = """
result = client.old_method("hello")
"""

edit_plan = {
    "migration_required": True,
    "targets": [
        {
            "target_code": 'client.old_method("hello")',
            "edits": [
                {
                    "target": "method_name",
                    "operation": "replace",
                    "value": {
                        "type": "identifier",
                        "name": "new_method"
                    }
                },
                {
                    "target": "arguments",
                    "operation": "replace",
                    "value": [
                        {
                            "type": "keyword_argument",
                            "name": "options",
                            "value": {
                                "type": "dictionary",
                                "entries": [
                                    {
                                        "key": "timeout",
                                        "value": {
                                            "type": "integer",
                                            "value": 30
                                        }
                                    },
                                    {
                                        "key": "features",
                                        "value": {
                                            "type": "tuple",
                                            "elements": [
                                                {
                                                    "type": "string",
                                                    "value": "a"
                                                },
                                                {
                                                    "type": "string",
                                                    "value": "b"
                                                }
                                            ]
                                        }
                                    }
                                ]
                            }
                        }
                    ]
                }
            ]
        }
    ],
    "manual_review": []
}

print("===== ORIGINAL CODE =====")
print(source_code)

migrated_code = engine.migrate_with_edit_plan(
    source_code,
    edit_plan
)

print("===== MIGRATED CODE =====")
print(migrated_code)

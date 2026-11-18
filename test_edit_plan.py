
import json

from agent2.migration_advisor import MigrationAdvisor


source_code = """
def ask_model(prompt):
    result = client.run(prompt)
    return result
"""

candidate = {
    "type": "usage",
    "code": "client.run(prompt)",
    "symbol": "run"
}

documentation = [
    {
        "text": """
Migration rule:
The deprecated run(prompt) method should be replaced with
invoke({"input": prompt}).

The invoke method accepts the input as a dictionary
with the key "input".
"""
    }
]

advisor = MigrationAdvisor()

edit_plan = advisor.create_edit_plan(
    source_code=source_code,
    candidate=candidate,
    documentation=documentation
)

print("===== MIGRATION EDIT PLAN =====")
print(json.dumps(edit_plan, indent=4))

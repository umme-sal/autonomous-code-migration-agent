from agent2.edit_plan_validator import EditPlanValidator
from copy import deepcopy

source_code = """
def ask_model(prompt):
    result = client.run(prompt)
    return result
"""

edit_plan = {
    "migration_required": True,
    "reason": "Replace run with invoke",
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

validator = EditPlanValidator()

result = validator.validate(source_code, edit_plan)

print("Validation result:")
print(result)

# Test 1: Target does not exist
invalid_target_plan = deepcopy(edit_plan)
invalid_target_plan["targets"][0]["target_code"] = "client.delete(prompt)"

print("\n===== TEST 1: INVALID TARGET =====")
print(validator.validate(source_code, invalid_target_plan))


# Test 2: Unsupported operation
invalid_operation_plan = deepcopy(edit_plan)
invalid_operation_plan["targets"][0]["edits"][0]["operation"] = "delete"

print("\n===== TEST 2: INVALID OPERATION =====")
print(validator.validate(source_code, invalid_operation_plan))


# Test 3: Conflicting edits
conflict_plan = deepcopy(edit_plan)
conflict_plan["targets"][0]["edits"].append({
    "target": "method_name",
    "operation": "replace",
    "value": {
        "type": "identifier",
        "name": "execute"
    }
})

print("\n===== TEST 3: CONFLICTING EDITS =====")
print(validator.validate(source_code, conflict_plan))

# Test 4: Ambiguous target (same call appears twice)

duplicate_source = """
def first():
    return client.run(prompt)

def second():
    return client.run(prompt)
"""

print("\n===== TEST 4: AMBIGUOUS TARGET =====")
print(validator.validate(duplicate_source, edit_plan))
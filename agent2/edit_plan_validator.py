import ast
import libcst as cst


def _call_structure(source: str):
    """Parse a call expression and return a whitespace-independent AST dump."""
    parsed = ast.parse(source, mode="eval")
    if not isinstance(parsed.body, ast.Call):
        raise ValueError("Target must be a function call expression.")
    return ast.dump(parsed.body, include_attributes=False)


class CallCounter(cst.CSTVisitor):

    def __init__(self):
        self.calls = {}

    def visit_Call(self, node):
        code = cst.Module([]).code_for_node(node).strip()

        try:
            key = _call_structure(code)
        except (SyntaxError, ValueError):
            return

        self.calls[key] = self.calls.get(key, 0) + 1


class EditPlanValidator:

    SUPPORTED_TARGETS = {
        "method_name",
        "arguments"
    }

    SUPPORTED_OPERATIONS = {
        "replace"
    }

    SUPPORTED_EXPRESSION_TYPES = {
        "identifier",
        "string",
        "integer",
        "float",
        "boolean",
        "none",
        "dictionary",
        "list",
        "tuple",
        "attribute",
        "call"
    }

    def validate(self, source_code: str, edit_plan: dict) -> dict:
        errors = []

        if not isinstance(edit_plan, dict):
            return {
                "valid": False,
                "errors": ["Edit plan must be a dictionary."]
            }

        if not isinstance(edit_plan.get("migration_required"), bool):
            errors.append("migration_required must be a boolean.")

        targets = edit_plan.get("targets")

        if not isinstance(targets, list):
            errors.append("targets must be a list.")
            return {"valid": False, "errors": errors}

        manual_review = edit_plan.get("manual_review", [])

        if not isinstance(manual_review, list):
            errors.append("manual_review must be a list.")
        elif not all(isinstance(item, str) for item in manual_review):
            errors.append("Every manual_review entry must be a string.")

        if errors:
            return {"valid": False, "errors": errors}

        if edit_plan["migration_required"] is False:
            if targets:
                errors.append(
                    "migration_required is false but targets is not empty."
                )
            return {"valid": len(errors) == 0, "errors": errors}

        if not targets:
            errors.append("migration_required is true but targets is empty.")
            return {"valid": False, "errors": errors}

        try:
            source_tree = cst.parse_module(source_code)
        except Exception as error:
            return {
                "valid": False,
                "errors": [f"Source code parsing failed: {error}"]
            }

        call_counter = CallCounter()
        source_tree.visit(call_counter)

        seen_targets = set()

        for target_index, target in enumerate(targets):
            if not isinstance(target, dict):
                errors.append(f"Target {target_index} must be a dictionary.")
                continue

            target_code = target.get("target_code")

            if not isinstance(target_code, str) or not target_code.strip():
                errors.append(f"Target {target_index} has invalid target_code.")
                continue

            target_code = target_code.strip()

            try:
                structural_key = _call_structure(target_code)
            except (SyntaxError, ValueError):
                errors.append(
                    f"Target {target_index} is not a valid call expression: {target_code}"
                )
                continue

            occurrences = call_counter.calls.get(structural_key, 0)

            if occurrences == 0:
                errors.append(
                    f"Target code not found structurally in source: {target_code}"
                )
            elif occurrences > 1:
                errors.append(
                    f"Ambiguous target: '{target_code}' appears "
                    f"{occurrences} times in source."
                )

            if structural_key in seen_targets:
                errors.append(f"Duplicate target detected: {target_code}")

            seen_targets.add(structural_key)

            edits = target.get("edits")

            if not isinstance(edits, list) or not edits:
                errors.append(
                    f"Target '{target_code}' must contain a non-empty edits list."
                )
                continue

            seen_edit_types = set()

            for edit_index, edit in enumerate(edits):
                if not isinstance(edit, dict):
                    errors.append(
                        f"Edit {edit_index} of '{target_code}' must be a dictionary."
                    )
                    continue

                edit_target = edit.get("target")
                operation = edit.get("operation")
                value = edit.get("value")

                if edit_target not in self.SUPPORTED_TARGETS:
                    errors.append(f"Unsupported edit target: {edit_target}")
                    continue

                if operation not in self.SUPPORTED_OPERATIONS:
                    errors.append(f"Unsupported operation: {operation}")
                    continue

                if edit_target in seen_edit_types:
                    errors.append(
                        f"Conflicting edits to '{edit_target}' in target '{target_code}'."
                    )

                seen_edit_types.add(edit_target)

                if edit_target == "method_name":
                    if not isinstance(value, dict):
                        errors.append("method_name replacement must be a dictionary.")
                    elif value.get("type") != "identifier":
                        errors.append("method_name must be replaced with an identifier.")
                    elif (
                        not isinstance(value.get("name"), str)
                        or not value["name"].isidentifier()
                    ):
                        errors.append("Invalid method name identifier.")

                elif edit_target == "arguments":
                    if not isinstance(value, list):
                        errors.append("arguments replacement must be a list.")
                        continue

                    for argument_index, argument in enumerate(value):
                        if not isinstance(argument, dict):
                            errors.append(
                                f"Argument {argument_index} must be a dictionary."
                            )
                            continue

                        argument_type = argument.get("type")

                        if argument_type == "keyword_argument":
                            name = argument.get("name")
                            if not isinstance(name, str) or not name.isidentifier():
                                errors.append(
                                    f"Invalid keyword argument name: {name}"
                                )
                        elif argument_type != "positional_argument":
                            errors.append(
                                f"Unsupported argument type: {argument_type}"
                            )
                            continue

                        self._validate_expression(
                            argument.get("value"),
                            errors,
                            f"Argument {argument_index}"
                        )

        return {
            "valid": len(errors) == 0,
            "errors": errors
        }

    def _validate_expression(self, expression, errors, location):
        if not isinstance(expression, dict):
            errors.append(f"{location}: expression must be a dictionary.")
            return

        expression_type = expression.get("type")

        if expression_type not in self.SUPPORTED_EXPRESSION_TYPES:
            errors.append(
                f"{location}: unsupported expression type '{expression_type}'."
            )
            return

        if expression_type == "identifier":
            name = expression.get("name")
            if not isinstance(name, str) or not name.isidentifier():
                errors.append(f"{location}: invalid identifier.")

        elif expression_type == "string":
            if not isinstance(expression.get("value"), str):
                errors.append(f"{location}: string value must be a string.")

        elif expression_type == "integer":
            value = expression.get("value")
            if not isinstance(value, int) or isinstance(value, bool):
                errors.append(f"{location}: integer value must be an integer.")

        elif expression_type == "float":
            value = expression.get("value")
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                errors.append(f"{location}: float value must be numeric.")

        elif expression_type == "boolean":
            if not isinstance(expression.get("value"), bool):
                errors.append(f"{location}: boolean value must be true or false.")

        elif expression_type == "none":
            pass

        elif expression_type in {"list", "tuple"}:
            elements = expression.get("elements")
            if not isinstance(elements, list):
                errors.append(f"{location}: elements must be a list.")
                return

            for index, element in enumerate(elements):
                self._validate_expression(
                    element, errors, f"{location}.elements[{index}]"
                )

        elif expression_type == "dictionary":
            entries = expression.get("entries")
            if not isinstance(entries, list):
                errors.append(f"{location}: dictionary entries must be a list.")
                return

            for index, entry in enumerate(entries):
                if not isinstance(entry, dict):
                    errors.append(
                        f"{location}: dictionary entry {index} must be a dictionary."
                    )
                    continue

                if not isinstance(entry.get("key"), str):
                    errors.append(f"{location}: dictionary key must be a string.")

                self._validate_expression(
                    entry.get("value"),
                    errors,
                    f"{location}.entries[{index}].value"
                )

        elif expression_type == "attribute":
            self._validate_expression(
                expression.get("value"), errors, f"{location}.value"
            )
            attr = expression.get("attr")
            if not isinstance(attr, str) or not attr.isidentifier():
                errors.append(f"{location}: invalid attribute name.")

        elif expression_type == "call":
            self._validate_expression(
                expression.get("function"), errors, f"{location}.function"
            )

            arguments = expression.get("arguments", [])
            if not isinstance(arguments, list):
                errors.append(f"{location}: call arguments must be a list.")
                return

            for index, argument in enumerate(arguments):
                if not isinstance(argument, dict):
                    errors.append(
                        f"{location}: call argument {index} must be a dictionary."
                    )
                    continue

                argument_type = argument.get("type")

                if argument_type == "keyword_argument":
                    name = argument.get("name")
                    if not isinstance(name, str) or not name.isidentifier():
                        errors.append(f"{location}: invalid keyword argument name.")
                elif argument_type != "positional_argument":
                    errors.append(f"{location}: unsupported call argument type.")
                    continue

                self._validate_expression(
                    argument.get("value"),
                    errors,
                    f"{location}.arguments[{index}]"
                )

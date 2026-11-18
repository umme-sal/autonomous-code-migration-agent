
import libcst as cst


class CallCounter(cst.CSTVisitor):

    def __init__(self):
        self.calls = {}

    def visit_Call(self, node):
        code = cst.Module([]).code_for_node(node).strip()
        self.calls[code] = self.calls.get(code, 0) + 1


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
        "number",
        "boolean",
        "none",
        "dictionary",
        "list",
        "attribute",
        "call"
    }

    def validate(self, source_code: str, edit_plan: dict) -> dict:

        errors = []

        # 1. Validate top-level structure
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

            return {
                "valid": False,
                "errors": errors
            }

        if edit_plan.get("migration_required") is False:
            return {
                "valid": len(errors) == 0,
                "errors": errors
            }

        # 2. Parse source code
        try:
            source_tree = cst.parse_module(source_code)

        except Exception as error:
            return {
                "valid": False,
                "errors": [
                    f"Source code parsing failed: {error}"
                ]
            }

        # 3. Count function calls
        call_counter = CallCounter()
        source_tree.visit(call_counter)

        # 4. Validate targets
        seen_targets = set()

        for target_index, target in enumerate(targets):

            if not isinstance(target, dict):
                errors.append(
                    f"Target {target_index} must be a dictionary."
                )
                continue

            target_code = target.get("target_code")

            if not isinstance(target_code, str) or not target_code.strip():
                errors.append(
                    f"Target {target_index} has invalid target_code."
                )
                continue

            target_code = target_code.strip()

            occurrences = call_counter.calls.get(target_code, 0)

            if occurrences == 0:
                errors.append(
                    f"Target code not found in source: {target_code}"
                )

            elif occurrences > 1:
                errors.append(
                    f"Ambiguous target: '{target_code}' appears "
                    f"{occurrences} times in source."
                )

            if target_code in seen_targets:
                errors.append(
                    f"Duplicate target detected: {target_code}"
                )

            seen_targets.add(target_code)

            edits = target.get("edits")

            if not isinstance(edits, list) or not edits:
                errors.append(
                    f"Target '{target_code}' must contain "
                    "a non-empty edits list."
                )
                continue

            seen_edit_types = set()

            # 5. Validate individual edits
            for edit_index, edit in enumerate(edits):

                if not isinstance(edit, dict):
                    errors.append(
                        f"Edit {edit_index} of '{target_code}' "
                        "must be a dictionary."
                    )
                    continue

                edit_target = edit.get("target")
                operation = edit.get("operation")
                value = edit.get("value")

                if edit_target not in self.SUPPORTED_TARGETS:
                    errors.append(
                        f"Unsupported edit target: {edit_target}"
                    )
                    continue

                if operation not in self.SUPPORTED_OPERATIONS:
                    errors.append(
                        f"Unsupported operation: {operation}"
                    )
                    continue

                if edit_target in seen_edit_types:
                    errors.append(
                        f"Conflicting edits to '{edit_target}' "
                        f"in target '{target_code}'."
                    )

                seen_edit_types.add(edit_target)

                # 6. Validate method name
                if edit_target == "method_name":

                    if not isinstance(value, dict):
                        errors.append(
                            "method_name replacement must be a dictionary."
                        )

                    elif value.get("type") != "identifier":
                        errors.append(
                            "method_name must be replaced with an identifier."
                        )

                    elif (
                        not isinstance(value.get("name"), str)
                        or not value["name"].isidentifier()
                    ):
                        errors.append(
                            "Invalid method name identifier."
                        )

                # 7. Validate arguments
                elif edit_target == "arguments":

                    if not isinstance(value, list):
                        errors.append(
                            "arguments replacement must be a list."
                        )

                    else:

                        for argument_index, argument in enumerate(value):

                            if not isinstance(argument, dict):
                                errors.append(
                                    f"Argument {argument_index} "
                                    "must be a dictionary."
                                )
                                continue

                            argument_type = argument.get("type")

                            if argument_type == "keyword_argument":

                                name = argument.get("name")

                                if (
                                    not isinstance(name, str)
                                    or not name.isidentifier()
                                ):
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

        # IMPORTANT: This return must be outside both loops.
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }

    def _validate_expression(self, expression, errors, location):

        if not isinstance(expression, dict):
            errors.append(
                f"{location}: expression must be a dictionary."
            )
            return

        expression_type = expression.get("type")

        if expression_type not in self.SUPPORTED_EXPRESSION_TYPES:
            errors.append(
                f"{location}: unsupported expression type "
                f"'{expression_type}'."
            )
            return

        # Identifier
        if expression_type == "identifier":

            name = expression.get("name")

            if not isinstance(name, str) or not name.isidentifier():
                errors.append(
                    f"{location}: invalid identifier."
                )

        # String
        elif expression_type == "string":

            if not isinstance(expression.get("value"), str):
                errors.append(
                    f"{location}: string value must be a string."
                )

        # Number
        elif expression_type == "number":

            value = expression.get("value")

            if (
                not isinstance(value, (int, float))
                or isinstance(value, bool)
            ):
                errors.append(
                    f"{location}: number value must be numeric."
                )

        # Boolean
        elif expression_type == "boolean":

            if not isinstance(expression.get("value"), bool):
                errors.append(
                    f"{location}: boolean value must be true or false."
                )

        # None
        elif expression_type == "none":
            pass

        # List
        elif expression_type == "list":

            elements = expression.get("elements")

            if not isinstance(elements, list):
                errors.append(
                    f"{location}: list elements must be a list."
                )
                return

            for index, element in enumerate(elements):

                self._validate_expression(
                    element,
                    errors,
                    f"{location}.elements[{index}]"
                )

        # Dictionary
        elif expression_type == "dictionary":

            entries = expression.get("entries")

            if not isinstance(entries, list):
                errors.append(
                    f"{location}: dictionary entries must be a list."
                )
                return

            for index, entry in enumerate(entries):

                if not isinstance(entry, dict):
                    errors.append(
                        f"{location}: dictionary entry "
                        f"{index} must be a dictionary."
                    )
                    continue

                if not isinstance(entry.get("key"), str):
                    errors.append(
                        f"{location}: dictionary key must be a string."
                    )

                self._validate_expression(
                    entry.get("value"),
                    errors,
                    f"{location}.entries[{index}].value"
                )

        # Attribute
        elif expression_type == "attribute":

            self._validate_expression(
                expression.get("value"),
                errors,
                f"{location}.value"
            )

            attr = expression.get("attr")

            if not isinstance(attr, str) or not attr.isidentifier():
                errors.append(
                    f"{location}: invalid attribute name."
                )

        # Call
        elif expression_type == "call":

            self._validate_expression(
                expression.get("function"),
                errors,
                f"{location}.function"
            )

            arguments = expression.get("arguments", [])

            if not isinstance(arguments, list):
                errors.append(
                    f"{location}: call arguments must be a list."
                )
                return

            for index, argument in enumerate(arguments):

                if not isinstance(argument, dict):
                    errors.append(
                        f"{location}: call argument {index} "
                        "must be a dictionary."
                    )
                    continue

                argument_type = argument.get("type")

                if argument_type == "keyword_argument":

                    name = argument.get("name")

                    if not isinstance(name, str) or not name.isidentifier():
                        errors.append(
                            f"{location}: invalid keyword argument name."
                        )

                elif argument_type != "positional_argument":

                    errors.append(
                        f"{location}: unsupported call argument type."
                    )
                    continue

                self._validate_expression(
                    argument.get("value"),
                    errors,
                    f"{location}.arguments[{index}]"
                )

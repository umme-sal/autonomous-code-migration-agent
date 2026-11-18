
import ast
import libcst as cst

from agent2.edit_plan_validator import EditPlanValidator


class ImportMigrationTransformer(cst.CSTTransformer):

    def __init__(self, migration_map):
        self.migration_map = migration_map

    def leave_ImportFrom(self, original_node, updated_node):

        old_module = original_node.module

        if isinstance(old_module, cst.Name):

            module_name = old_module.value

            if module_name in self.migration_map:

                new_module = self.migration_map[module_name]

                return updated_node.with_changes(
                    module=cst.parse_expression(new_module)
                )

        return updated_node


class ReferenceMigrationTransformer(cst.CSTTransformer):

    def __init__(self, migration_map):
        self.migration_map = migration_map

    def leave_Name(self, original_node, updated_node):

        old_name = original_node.value

        if old_name in self.migration_map:

            return updated_node.with_changes(
                value=self.migration_map[old_name]
            )

        return updated_node


class EditPlanTransformer(cst.CSTTransformer):

    def __init__(self, edit_plan):

        self.edit_plan = edit_plan

        # Stores (target_index, edit_index) for applied edits
        self.applied_edits = set()

    def leave_Call(self, original_node, updated_node):

        # Get the exact original call representation
        original_call = cst.Module([]).code_for_node(
            original_node
        ).strip()

        new_node = updated_node

        for target_index, target in enumerate(
            self.edit_plan.get("targets", [])
        ):

            target_code = target.get("target_code", "").strip()

            # Process only the matching call
            if original_call != target_code:
                continue

            for edit_index, edit in enumerate(
                target.get("edits", [])
            ):

                edit_target = edit.get("target")
                operation = edit.get("operation")
                value = edit.get("value")

                if operation != "replace":
                    raise ValueError(
                        f"Unsupported operation: {operation}"
                    )

                # Method name replacement
                if edit_target == "method_name":

                    if not isinstance(new_node.func, cst.Attribute):
                        raise ValueError(
                            f"Cannot replace method name in: {target_code}"
                        )

                    new_node = new_node.with_changes(
                        func=new_node.func.with_changes(
                            attr=cst.Name(
                                value=value["name"]
                            )
                        )
                    )

                # Argument replacement
                elif edit_target == "arguments":

                    new_arguments = []

                    for argument in value:

                        argument_type = argument.get("type")

                        argument_value = self._build_expression(
                            argument["value"]
                        )

                        if argument_type == "positional_argument":

                            new_arguments.append(
                                cst.Arg(
                                    value=argument_value
                                )
                            )

                        elif argument_type == "keyword_argument":

                            new_arguments.append(
                                cst.Arg(
                                    value=argument_value,
                                    keyword=cst.Name(
                                        value=argument["name"]
                                    )
                                )
                            )

                        else:
                            raise ValueError(
                                f"Unsupported argument type: {argument_type}"
                            )

                    new_node = new_node.with_changes(
                        args=new_arguments
                    )

                else:
                    raise ValueError(
                        f"Unsupported edit target: {edit_target}"
                    )

                # Record successfully processed edit
                self.applied_edits.add(
                    (target_index, edit_index)
                )

        return new_node

    def _build_expression(self, expression):

        expression_type = expression.get("type")

        # Identifier
        if expression_type == "identifier":

            return cst.Name(
                value=expression["name"]
            )

        # String
        elif expression_type == "string":

            return cst.SimpleString(
                repr(expression["value"])
            )

        # Number
        elif expression_type == "number":

            return cst.parse_expression(
                str(expression["value"])
            )

        # Boolean
        elif expression_type == "boolean":

            return cst.Name(
                value="True" if expression["value"] else "False"
            )

        # None
        elif expression_type == "none":

            return cst.Name(
                value="None"
            )

        # Dictionary
        elif expression_type == "dictionary":

            entries = []

            for entry in expression["entries"]:

                key = cst.SimpleString(
                    repr(entry["key"])
                )

                value = self._build_expression(
                    entry["value"]
                )

                entries.append(
                    cst.DictElement(
                        key=key,
                        value=value
                    )
                )

            return cst.Dict(
                elements=entries
            )

        # List
        elif expression_type == "list":

            elements = []

            for element in expression["elements"]:

                elements.append(
                    cst.Element(
                        value=self._build_expression(element)
                    )
                )

            return cst.List(
                elements=elements
            )

        # Attribute
        elif expression_type == "attribute":

            return cst.Attribute(
                value=self._build_expression(
                    expression["value"]
                ),
                attr=cst.Name(
                    value=expression["attr"]
                )
            )

        # Function call
        elif expression_type == "call":

            function = self._build_expression(
                expression["function"]
            )

            arguments = []

            for argument in expression.get("arguments", []):

                argument_type = argument.get("type")

                argument_value = self._build_expression(
                    argument["value"]
                )

                if argument_type == "positional_argument":

                    arguments.append(
                        cst.Arg(
                            value=argument_value
                        )
                    )

                elif argument_type == "keyword_argument":

                    arguments.append(
                        cst.Arg(
                            value=argument_value,
                            keyword=cst.Name(
                                value=argument["name"]
                            )
                        )
                    )

                else:
                    raise ValueError(
                        f"Unsupported call argument type: {argument_type}"
                    )

            return cst.Call(
                func=function,
                args=arguments
            )

        else:

            raise ValueError(
                f"Unsupported expression type: {expression_type}"
            )


class MigrationEngine:

    def __init__(self):
        self.plan_validator = EditPlanValidator()

    def migrate(self, source_code: str, migration_map: dict) -> str:

        tree = cst.parse_module(source_code)

        transformer = ImportMigrationTransformer(
            migration_map
        )

        modified_tree = tree.visit(transformer)

        return modified_tree.code

    def migrate_with_edit_plan(
        self,
        source_code: str,
        edit_plan: dict
    ) -> str:

        # Step 1: Validate edit plan
        validation_result = self.plan_validator.validate(
            source_code,
            edit_plan
        )

        if not validation_result["valid"]:

            raise ValueError(
                "Invalid migration plan:\n"
                + "\n".join(validation_result["errors"])
            )

        # Step 2: Return original code if migration is not required
        if not edit_plan["migration_required"]:
            return source_code

        # Step 3: Parse source code
        tree = cst.parse_module(source_code)

        # Step 4: Apply migration edits
        transformer = EditPlanTransformer(
            edit_plan
        )

        modified_tree = tree.visit(transformer)

        # Step 5: Count requested edits
        total_edits = sum(
            len(target.get("edits", []))
            for target in edit_plan.get("targets", [])
        )

        applied_edits = len(transformer.applied_edits)

        # Step 6: Verify every requested edit was applied
        if applied_edits != total_edits:

            missing_edits = []

            for target_index, target in enumerate(
                edit_plan.get("targets", [])
            ):

                for edit_index, edit in enumerate(
                    target.get("edits", [])
                ):

                    if (
                        target_index,
                        edit_index
                    ) not in transformer.applied_edits:

                        missing_edits.append({
                            "target": target.get("target_code"),
                            "edit_index": edit_index
                        })

            raise ValueError(
                "Migration verification failed.\n"
                f"Total requested edits: {total_edits}\n"
                f"Successfully applied edits: {applied_edits}\n"
                f"Missing edits: {missing_edits}"
            )

        # Step 7: Get migrated code
        migrated_code = modified_tree.code

        # Step 8: Validate Python syntax
        try:

            ast.parse(migrated_code)

        except SyntaxError as error:

            raise ValueError(
                "Migration produced invalid Python syntax:\n"
                f"Line: {error.lineno}\n"
                f"Error: {error.msg}"
            ) from error

        # Step 9: Return migrated code
        return migrated_code


import ast
import libcst as cst

from agent2.edit_plan_validator import EditPlanValidator


class ImportMigrationTransformer(cst.CSTTransformer):

    def __init__(self, migration_rules):

        self.module_map = {}
        self.symbol_map = {}

        for rule in migration_rules:

            source_module = rule.get("source_module")
            target_module = rule.get("target_module")

            source_symbol = rule.get("source")
            target_symbol = rule.get("target")

            if source_module and target_module:
                self.module_map[source_module] = target_module

            if (
                source_module
                and target_module
                and source_symbol
                and target_symbol
                and source_symbol != target_symbol
            ):
                self.symbol_map[
                    (source_module, source_symbol)
                ] = target_symbol

    def leave_ImportFrom(self, original_node, updated_node):

        if original_node.module is None:
            return updated_node

        old_module = cst.Module([]).code_for_node(
            original_node.module
        ).strip()

        new_module = self.module_map.get(
            old_module,
            old_module
        )

        new_names = []

        for alias in updated_node.names:

            if isinstance(alias, cst.ImportStar):
                new_names.append(alias)
                continue

            if isinstance(alias.name, cst.Name):

                old_symbol = alias.name.value

                new_symbol = self.symbol_map.get(
                    (old_module, old_symbol)
                )

                if new_symbol:

                    # Preserve the original local name when aliased.
                    # Example: import initialize_agent as old_agent
                    # becomes: import create_agent as old_agent
                    alias = alias.with_changes(
                        name=cst.Name(new_symbol)
                    )

            new_names.append(alias)

        return updated_node.with_changes(
            module=cst.parse_expression(new_module),
            names=new_names
        )


class SymbolReferenceTransformer(cst.CSTTransformer):

    def __init__(self, symbol_aliases):

        self.symbol_aliases = symbol_aliases

    def leave_Name(self, original_node, updated_node):

        old_name = original_node.value

        if old_name in self.symbol_aliases:

            return updated_node.with_changes(
                value=self.symbol_aliases[old_name]
            )

        return updated_node


class EditPlanTransformer(cst.CSTTransformer):

    def __init__(self, edit_plan):

        self.edit_plan = edit_plan
        self.applied_edits = set()

    def leave_Call(self, original_node, updated_node):

        original_call = cst.Module([]).code_for_node(
            original_node
        ).strip()

        new_node = updated_node

        for target_index, target in enumerate(
            self.edit_plan.get("targets", [])
        ):

            target_code = target.get(
                "target_code", ""
            ).strip()

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

                if edit_target == "method_name":

                    if not isinstance(new_node.func, cst.Attribute):
                        raise ValueError(
                            f"Cannot replace method name in: {target_code}"
                        )

                    new_node = new_node.with_changes(
                        func=new_node.func.with_changes(
                            attr=cst.Name(value=value["name"])
                        )
                    )

                elif edit_target == "arguments":

                    new_arguments = []

                    for argument in value:

                        argument_value = self._build_expression(
                            argument["value"]
                        )

                        if argument["type"] == "positional_argument":

                            new_arguments.append(
                                cst.Arg(value=argument_value)
                            )

                        elif argument["type"] == "keyword_argument":

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
                                "Unsupported argument type."
                            )

                    new_node = new_node.with_changes(
                        args=new_arguments
                    )

                else:
                    raise ValueError(
                        f"Unsupported edit target: {edit_target}"
                    )

                self.applied_edits.add(
                    (target_index, edit_index)
                )

        return new_node

    def _build_expression(self, expression):

        expression_type = expression.get("type")

        if expression_type == "identifier":
            return cst.Name(value=expression["name"])

        elif expression_type == "string":
            return cst.SimpleString(
                repr(expression["value"])
            )

        elif expression_type == "number":
            return cst.parse_expression(
                str(expression["value"])
            )

        elif expression_type == "boolean":
            return cst.Name(
                value="True" if expression["value"] else "False"
            )

        elif expression_type == "none":
            return cst.Name(value="None")

        elif expression_type == "dictionary":

            entries = []

            for entry in expression["entries"]:

                entries.append(
                    cst.DictElement(
                        key=cst.SimpleString(
                            repr(entry["key"])
                        ),
                        value=self._build_expression(
                            entry["value"]
                        )
                    )
                )

            return cst.Dict(elements=entries)

        elif expression_type == "list":

            return cst.List(
                elements=[
                    cst.Element(
                        value=self._build_expression(element)
                    )
                    for element in expression["elements"]
                ]
            )

        elif expression_type == "attribute":

            return cst.Attribute(
                value=self._build_expression(
                    expression["value"]
                ),
                attr=cst.Name(
                    value=expression["attr"]
                )
            )

        elif expression_type == "call":

            arguments = []

            for argument in expression.get("arguments", []):

                argument_value = self._build_expression(
                    argument["value"]
                )

                if argument["type"] == "positional_argument":

                    arguments.append(
                        cst.Arg(value=argument_value)
                    )

                elif argument["type"] == "keyword_argument":

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
                        "Unsupported call argument type."
                    )

            return cst.Call(
                func=self._build_expression(
                    expression["function"]
                ),
                args=arguments
            )

        raise ValueError(
            f"Unsupported expression type: {expression_type}"
        )


class MigrationEngine:

    def __init__(self):
        self.plan_validator = EditPlanValidator()

    def build_migration_map(self, migration_rules: list[dict]) -> dict:

        migration_map = {}

        for rule in migration_rules:

            source_module = rule.get("source_module")
            target_module = rule.get("target_module")

            if (
                source_module
                and target_module
                and source_module != target_module
            ):
                migration_map[source_module] = target_module

        return migration_map

    def migrate(self, source_code: str, migration_rules: list[dict]) -> str:

        tree = cst.parse_module(source_code)

        # First identify aliases and construct the symbol mapping.
        symbol_aliases = {}

        for statement in tree.body:

            if not isinstance(statement, cst.SimpleStatementLine):
                continue

            for small_statement in statement.body:

                if not isinstance(small_statement, cst.ImportFrom):
                    continue

                if small_statement.module is None:
                    continue

                old_module = cst.Module([]).code_for_node(
                    small_statement.module
                ).strip()

                for alias in small_statement.names:

                    if not isinstance(alias, cst.ImportAlias):
                        continue

                    if not isinstance(alias.name, cst.Name):
                        continue

                    old_symbol = alias.name.value

                    for rule in migration_rules:

                        if (
                            rule.get("source_module") == old_module
                            and rule.get("source") == old_symbol
                            and rule.get("target_module") == old_module
                            and rule.get("target") != old_symbol
                        ):

                            local_name = (
                                alias.asname.name.value
                                if alias.asname
                                else old_symbol
                            )

                            symbol_aliases[local_name] = (
                                rule["target"]
                                if not alias.asname
                                else local_name
                            )

        # Apply module and imported-symbol changes.
        import_transformer = ImportMigrationTransformer(
            migration_rules
        )

        modified_tree = tree.visit(import_transformer)

        # Update references only for unaliased imports.
        if symbol_aliases:

            reference_transformer = SymbolReferenceTransformer(
                symbol_aliases
            )

            modified_tree = modified_tree.visit(
                reference_transformer
            )

        migrated_code = modified_tree.code

        ast.parse(migrated_code)

        return migrated_code

    def migrate_with_edit_plan(
        self,
        source_code: str,
        edit_plan: dict
    ) -> str:

        validation_result = self.plan_validator.validate(
            source_code,
            edit_plan
        )

        if not validation_result["valid"]:

            raise ValueError(
                "Invalid migration plan:\n"
                + "\n".join(validation_result["errors"])
            )

        if not edit_plan["migration_required"]:
            return source_code

        tree = cst.parse_module(source_code)

        transformer = EditPlanTransformer(edit_plan)

        modified_tree = tree.visit(transformer)

        total_edits = sum(
            len(target.get("edits", []))
            for target in edit_plan.get("targets", [])
        )

        applied_edits = len(transformer.applied_edits)

        if applied_edits != total_edits:

            raise ValueError(
                "Migration verification failed.\n"
                f"Total requested edits: {total_edits}\n"
                f"Successfully applied edits: {applied_edits}"
            )

        migrated_code = modified_tree.code

        ast.parse(migrated_code)

        return migrated_code

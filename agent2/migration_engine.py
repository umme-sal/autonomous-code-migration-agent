import ast
import libcst as cst

from agent2.edit_plan_validator import EditPlanValidator


def _ast_dump_from_source(source: str) -> str:
    """Return a formatting-independent AST representation."""
    parsed = ast.parse(source, mode="eval")
    return ast.dump(parsed.body, include_attributes=False)


class ImportMigrationTransformer(cst.CSTTransformer):

    def __init__(self, migration_rules):
        self.symbol_migrations = {}

        for rule in migration_rules:
            source_module = rule.get("source_module")
            target_module = rule.get("target_module")
            source_symbol = rule.get("source")
            target_symbol = rule.get("target")

            if source_module and target_module and source_symbol and target_symbol:
                self.symbol_migrations[(source_module, source_symbol)] = {
                    "target_module": target_module,
                    "target_symbol": target_symbol
                }

    def leave_SimpleStatementLine(self, original_node, updated_node):
        if len(original_node.body) != 1:
            return updated_node

        original_import = original_node.body[0]

        if not isinstance(original_import, cst.ImportFrom):
            return updated_node

        if original_import.module is None or isinstance(original_import.names, cst.ImportStar):
            return updated_node

        old_module = cst.Module([]).code_for_node(original_import.module).strip()
        grouped_imports = {}

        for alias in original_import.names:
            if not isinstance(alias.name, cst.Name):
                grouped_imports.setdefault(old_module, []).append(alias)
                continue

            old_symbol = alias.name.value
            migration = self.symbol_migrations.get((old_module, old_symbol))

            if migration:
                target_module = migration["target_module"]
                new_alias = cst.ImportAlias(
                    name=cst.Name(migration["target_symbol"]),
                    asname=alias.asname
                )
            else:
                target_module = old_module
                new_alias = cst.ImportAlias(
                    name=alias.name,
                    asname=alias.asname
                )

            grouped_imports.setdefault(target_module, []).append(new_alias)

        new_statements = []

        for module_name, aliases in grouped_imports.items():
            new_statements.append(
                cst.ImportFrom(
                    module=cst.parse_expression(module_name),
                    names=aliases
                )
            )

        if not new_statements:
            return updated_node

        first_statement = updated_node.with_changes(body=[new_statements[0]])

        if len(new_statements) == 1:
            return first_statement

        remaining = [
            cst.SimpleStatementLine(body=[statement])
            for statement in new_statements[1:]
        ]

        return cst.FlattenSentinel([first_statement] + remaining)


class SymbolReferenceTransformer(cst.CSTTransformer):

    def __init__(self, symbol_aliases):
        self.symbol_aliases = symbol_aliases

    def leave_Name(self, original_node, updated_node):
        replacement = self.symbol_aliases.get(original_node.value)

        if replacement:
            return updated_node.with_changes(value=replacement)

        return updated_node


class EditPlanTransformer(cst.CSTTransformer):

    def __init__(self, edit_plan):
        self.edit_plan = edit_plan
        self.applied_edits = set()

    @staticmethod
    def _matches_target(original_node, target_code):
        """Compare call expressions by AST, ignoring whitespace/layout."""
        try:
            actual_code = cst.Module([]).code_for_node(original_node)
            return _ast_dump_from_source(actual_code) == _ast_dump_from_source(target_code)
        except (SyntaxError, TypeError, ValueError):
            return False

    def leave_Call(self, original_node, updated_node):
        new_node = updated_node

        for target_index, target in enumerate(self.edit_plan.get("targets", [])):
            target_code = target.get("target_code", "")

            if not self._matches_target(original_node, target_code):
                continue

            for edit_index, edit in enumerate(target.get("edits", [])):
                edit_target = edit.get("target")
                operation = edit.get("operation")
                value = edit.get("value")

                if operation != "replace":
                    raise ValueError(f"Unsupported operation: {operation}")

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
                        argument_value = self._build_expression(argument["value"])

                        if argument["type"] == "positional_argument":
                            new_arguments.append(cst.Arg(value=argument_value))

                        elif argument["type"] == "keyword_argument":
                            new_arguments.append(
                                cst.Arg(
                                    value=argument_value,
                                    keyword=cst.Name(value=argument["name"])
                                )
                            )
                        else:
                            raise ValueError("Unsupported argument type.")

                    new_node = new_node.with_changes(args=new_arguments)

                else:
                    raise ValueError(f"Unsupported edit target: {edit_target}")

                self.applied_edits.add((target_index, edit_index))

        return new_node

    def _build_expression(self, expression):
        expression_type = expression.get("type")

        if expression_type == "identifier":
            return cst.Name(value=expression["name"])

        if expression_type == "string":
            return cst.SimpleString(repr(expression["value"]))

        if expression_type == "integer":
            return cst.Integer(value=str(expression["value"]))

        if expression_type == "float":
            return cst.Float(value=str(expression["value"]))

        if expression_type == "boolean":
            return cst.Name(value="True" if expression["value"] else "False")

        if expression_type == "none":
            return cst.Name(value="None")

        if expression_type == "dictionary":
            return cst.Dict(
                elements=[
                    cst.DictElement(
                        key=cst.SimpleString(repr(entry["key"])),
                        value=self._build_expression(entry["value"])
                    )
                    for entry in expression["entries"]
                ]
            )

        if expression_type == "list":
            return cst.List(
                elements=[
                    cst.Element(value=self._build_expression(item))
                    for item in expression["elements"]
                ]
            )

        if expression_type == "tuple":
            return cst.Tuple(
                elements=[
                    cst.Element(value=self._build_expression(item))
                    for item in expression["elements"]
                ]
            )

        if expression_type == "attribute":
            return cst.Attribute(
                value=self._build_expression(expression["value"]),
                attr=cst.Name(value=expression["attr"])
            )

        if expression_type == "call":
            arguments = []

            for argument in expression.get("arguments", []):
                argument_value = self._build_expression(argument["value"])

                if argument["type"] == "positional_argument":
                    arguments.append(cst.Arg(value=argument_value))
                elif argument["type"] == "keyword_argument":
                    arguments.append(
                        cst.Arg(
                            value=argument_value,
                            keyword=cst.Name(value=argument["name"])
                        )
                    )
                else:
                    raise ValueError("Unsupported call argument type.")

            return cst.Call(
                func=self._build_expression(expression["function"]),
                args=arguments
            )

        raise ValueError(f"Unsupported expression type: {expression_type}")


class MigrationEngine:

    def __init__(self):
        self.plan_validator = EditPlanValidator()

    def build_migration_map(self, migration_rules: list[dict]) -> dict:
        migration_map = {}

        for rule in migration_rules:
            source_module = rule.get("source_module")
            target_module = rule.get("target_module")

            if source_module and target_module and source_module != target_module:
                migration_map[source_module] = target_module

        return migration_map

    def migrate(self, source_code: str, migration_rules: list[dict]) -> str:
        tree = cst.parse_module(source_code)
        symbol_aliases = {}

        for statement in tree.body:
            if not isinstance(statement, cst.SimpleStatementLine):
                continue

            for small_statement in statement.body:
                if not isinstance(small_statement, cst.ImportFrom):
                    continue

                if small_statement.module is None or isinstance(small_statement.names, cst.ImportStar):
                    continue

                old_module = cst.Module([]).code_for_node(small_statement.module).strip()

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
                            local_name = alias.asname.name.value if alias.asname else old_symbol
                            symbol_aliases[local_name] = (
                                rule["target"] if not alias.asname else local_name
                            )

        modified_tree = tree.visit(ImportMigrationTransformer(migration_rules))

        if symbol_aliases:
            modified_tree = modified_tree.visit(
                SymbolReferenceTransformer(symbol_aliases)
            )

        migrated_code = modified_tree.code
        ast.parse(migrated_code)
        return migrated_code

    def migrate_with_edit_plan(self, source_code: str, edit_plan: dict) -> str:
        validation_result = self.plan_validator.validate(source_code, edit_plan)

        if not validation_result["valid"]:
            raise ValueError(
                "Invalid migration plan:\n" + "\n".join(validation_result["errors"])
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


# ================================================================
# Async migration application (R18 / R19)
# ================================================================

class AsyncMigrationTransformer(cst.CSTTransformer):
    """Apply a validated, deterministic async operation plan."""

    def __init__(self, operations: dict):
        self.functions = set(operations.get("functions", []))
        self.await_keys = set()
        self.applied_awaits = set()
        for code in operations.get("await_calls", []):
            try:
                self.await_keys.add(_ast_dump_from_source(code))
            except (SyntaxError, TypeError, ValueError):
                raise ValueError(f"Invalid async call target: {code}")
        self.applied_functions = set()

    def leave_FunctionDef(self, original_node, updated_node):
        if original_node.name.value not in self.functions:
            return updated_node
        if original_node.asynchronous is not None:
            self.applied_functions.add(original_node.name.value)
            return updated_node
        self.applied_functions.add(original_node.name.value)
        return updated_node.with_changes(asynchronous=cst.Asynchronous())

    def leave_Call(self, original_node, updated_node):
        code = cst.Module([]).code_for_node(original_node).strip()
        try:
            key = _ast_dump_from_source(code)
        except (SyntaxError, TypeError, ValueError):
            return updated_node
        if key not in self.await_keys:
            return updated_node
        self.applied_awaits.add(key)
        return cst.Await(expression=updated_node)


def _migrate_with_edit_plan_and_async(self, source_code: str, edit_plan: dict) -> str:
    # First preserve and execute all pre-existing method/argument edits.
    migrated = MigrationEngine._migrate_with_edit_plan_standard(self, source_code, edit_plan)
    operations = edit_plan.get("async_operations") or {}
    functions = operations.get("functions", [])
    await_calls = operations.get("await_calls", [])
    if not functions and not await_calls:
        return migrated

    # Validate targets against the current code before changing anything.
    parsed = ast.parse(migrated)
    defined = {
        node.name
        for node in ast.walk(parsed)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    missing_functions = sorted(set(functions) - defined)
    if missing_functions:
        raise ValueError("Async migration references missing functions: " + ", ".join(missing_functions))

    tree = cst.parse_module(migrated)
    transformer = AsyncMigrationTransformer(operations)
    modified = tree.visit(transformer)

    if set(functions) - transformer.applied_functions:
        missing = sorted(set(functions) - transformer.applied_functions)
        raise ValueError("Failed to convert async functions: " + ", ".join(missing))
    if len(transformer.applied_awaits) != len(set(
        _ast_dump_from_source(item) for item in await_calls
    )):
        raise ValueError("One or more async call targets were not found or applied.")

    result = modified.code
    ast.parse(result)
    return result


MigrationEngine._migrate_with_edit_plan_standard = MigrationEngine.migrate_with_edit_plan
MigrationEngine.migrate_with_edit_plan = _migrate_with_edit_plan_and_async

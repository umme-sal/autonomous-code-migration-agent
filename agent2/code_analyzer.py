
import libcst as cst


class CodeAnalyzer(cst.CSTVisitor):

    def __init__(self, migration_rules: list[dict]):
        self.migration_rules = migration_rules

        self.imports = []
        self.functions = []
        self.classes = []

        self.migration_candidates = []
        self.imported_symbols = {}

        # Track nested functions
        self.function_stack = []

        # Store affected functions
        self.affected_functions = []

    # --------------------------------------------------
    # IMPORT DETECTION
    # --------------------------------------------------

    def visit_ImportFrom(self, node: cst.ImportFrom):

        import_code = cst.Module([]).code_for_node(node).strip()
        self.imports.append(import_code)

        if node.module is None:
            return

        module_name = self._get_attribute_name(node.module)

        for imported_name in node.names:

            if not isinstance(imported_name, cst.ImportAlias):
                continue

            symbol_name = self._get_attribute_name(
                imported_name.name
            )

            # Actual name used in the source code
            if imported_name.asname:
                local_name = imported_name.asname.name.value
            else:
                local_name = symbol_name

            rule = self._find_matching_rule(
                module_name,
                symbol_name
            )

            if rule:

                candidate = {
                    "type": "import",
                    "code": import_code,
                    "module": module_name,
                    "symbol": symbol_name,
                    "local_name": local_name,
                    "rule": rule
                }

                self.migration_candidates.append(candidate)

                # Store using the actual local name
                self.imported_symbols[local_name] = rule

    def visit_Import(self, node: cst.Import):

        import_code = cst.Module([]).code_for_node(node).strip()
        self.imports.append(import_code)

    # --------------------------------------------------
    # FUNCTION TRACKING
    # --------------------------------------------------

    def visit_FunctionDef(self, node: cst.FunctionDef):

        self.functions.append(node.name.value)

        self.function_stack.append(node)

    def leave_FunctionDef(self, original_node: cst.FunctionDef):

        self.function_stack.pop()

    # --------------------------------------------------
    # CLASS TRACKING
    # --------------------------------------------------

    def visit_ClassDef(self, node: cst.ClassDef):

        self.classes.append(node.name.value)

    # --------------------------------------------------
    # CALL DETECTION
    # --------------------------------------------------

    def visit_Call(self, node: cst.Call):

        symbol_name = self._get_attribute_base(node.func)

        if symbol_name not in self.imported_symbols:
            return

        rule = self.imported_symbols[symbol_name]

        call_code = cst.Module([]).code_for_node(node).strip()

        enclosing_function = None
        enclosing_function_code = None

        if self.function_stack:

            function_node = self.function_stack[-1]

            enclosing_function = function_node.name.value

            enclosing_function_code = (
                cst.Module([]).code_for_node(function_node)
            )

            # Avoid duplicate affected functions
            if not any(
                item["code"] == enclosing_function_code
                for item in self.affected_functions
            ):

                self.affected_functions.append({
                    "name": enclosing_function,
                    "code": enclosing_function_code
                })

        self.migration_candidates.append({
            "type": "usage",
            "code": call_code,
            "symbol": symbol_name,
            "rule": rule,
            "enclosing_function": enclosing_function,
            "enclosing_function_code": enclosing_function_code
        })

    # --------------------------------------------------
    # RULE MATCHING
    # --------------------------------------------------

    def _find_matching_rule(
        self,
        module_name: str,
        symbol_name: str
    ):

        for rule in self.migration_rules:

            if (
                rule.get("source_module") == module_name
                and rule.get("source") == symbol_name
            ):
                return rule

        return None

    # --------------------------------------------------
    # CST UTILITIES
    # --------------------------------------------------

    def _get_attribute_name(self, node):

        if isinstance(node, cst.Name):
            return node.value

        if isinstance(node, cst.Attribute):
            return (
                self._get_attribute_name(node.value)
                + "."
                + node.attr.value
            )

        return ""

    def _get_attribute_base(self, node):

        if isinstance(node, cst.Name):
            return node.value

        if isinstance(node, cst.Attribute):
            return self._get_attribute_base(node.value)

        return ""

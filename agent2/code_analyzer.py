import libcst as cst


class CodeAnalyzer(cst.CSTVisitor):

    def __init__(self, migration_rules: list[dict]):
        self.migration_rules = migration_rules

        self.imports = []
        self.functions = []
        self.classes = []

        self.migration_candidates = []

        # Symbols imported from modules that require migration
        self.imported_symbols = {}

    def visit_ImportFrom(self, node: cst.ImportFrom):

        import_code = cst.Module([]).code_for_node(node)

        self.imports.append(import_code)

        # Get module name
        if isinstance(node.module, cst.Name):
            module_name = node.module.value

        elif isinstance(node.module, cst.Attribute):
            module_name = self._get_attribute_name(node.module)

        else:
            return

        # Check imported symbols
        for imported_name in node.names:

            if not isinstance(imported_name, cst.ImportAlias):
                continue

            if isinstance(imported_name.name, cst.Name):
                symbol_name = imported_name.name.value

            elif isinstance(imported_name.name, cst.Attribute):
                symbol_name = self._get_attribute_name(
                    imported_name.name
                )

            else:
                continue

            # Find matching migration rule
            rule = self._find_matching_rule(
                module_name,
                symbol_name
            )

            if rule:

                # Store migration candidate for import
                self.migration_candidates.append({
                    "type": "import",
                    "code": import_code,
                    "module": module_name,
                    "symbol": symbol_name,
                    "rule": rule
                })

                # Remember imported symbol
                self.imported_symbols[symbol_name] = rule

    def visit_Import(self, node: cst.Import):

        import_code = cst.Module([]).code_for_node(node)

        self.imports.append(import_code)

    def visit_Name(self, node: cst.Name):
        return

    def visit_Call(self, node: cst.Call):

        # Example:
        # ChatOpenAI()
        # OpenAIEmbeddings()

        if isinstance(node.func, cst.Name):

            symbol_name = node.func.value

            if symbol_name in self.imported_symbols:

                rule = self.imported_symbols[symbol_name]

                code = cst.Module([]).code_for_node(node)

                self.migration_candidates.append({
                    "type": "usage",
                    "code": code,
                    "symbol": symbol_name,
                    "rule": rule
                })

        # Example:
        # FAISS.from_documents(...)
        elif isinstance(node.func, cst.Attribute):

            base_name = self._get_attribute_base(node.func)

            if base_name in self.imported_symbols:

                rule = self.imported_symbols[base_name]

                code = cst.Module([]).code_for_node(node)

                self.migration_candidates.append({
                    "type": "usage",
                    "code": code,
                    "symbol": base_name,
                    "rule": rule
                })

    def visit_FunctionDef(self, node: cst.FunctionDef):

        self.functions.append(node.name.value)

    def visit_ClassDef(self, node: cst.ClassDef):

        self.classes.append(node.name.value)

    def _find_matching_rule(
        self,
        module_name: str,
        symbol_name: str
    ):

        for rule in self.migration_rules:

            source_module = rule.get("source_module")
            source_symbol = rule.get("source")

            if (
                source_module == module_name
                and source_symbol == symbol_name
            ):
                return rule

        return None

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
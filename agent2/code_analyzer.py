import libcst as cst


class CodeAnalyzer(cst.CSTVisitor):

    def __init__(self):
        self.imports = []
        self.functions = []
        self.classes = []
        self.migration_candidates = []

    def visit_Import(self, node: cst.Import):

        import_code = cst.Module([]).code_for_node(node)

        self.imports.append(import_code)

        self.migration_candidates.append({
            "type": "import",
            "code": import_code
        })

    def visit_ImportFrom(self, node: cst.ImportFrom):

        import_code = cst.Module([]).code_for_node(node)

        self.imports.append(import_code)

        self.migration_candidates.append({
            "type": "import_from",
            "code": import_code
        })

    def visit_FunctionDef(
        self,
        node: cst.FunctionDef
    ):

        self.functions.append(
            node.name.value
        )

    def visit_ClassDef(
        self,
        node: cst.ClassDef
    ):

        self.classes.append(
            node.name.value
        )
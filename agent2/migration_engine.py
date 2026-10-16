import libcst as cst


class ImportMigrationTransformer(cst.CSTTransformer):

    def __init__(self, migration_map: dict):
        self.migration_map = migration_map
        self.renames = {}

    def leave_ImportFrom(
        self,
        original_node: cst.ImportFrom,
        updated_node: cst.ImportFrom
    ):

        # Get the complete module name.
        module_name = self._get_module_name(
            original_node.module
        )

        if module_name is None:
            return updated_node

        # Check whether this module has a migration rule.
        if module_name not in self.migration_map:
            return updated_node

        migration = self.migration_map[module_name]

        new_module = migration["module"]

        new_names = []

        for name in updated_node.names:

            if isinstance(name, cst.ImportAlias):

                old_name = self._get_name(
                    name.name
                )

                new_name = migration.get(
                    "names",
                    {}
                ).get(
                    old_name,
                    old_name
                )

                if old_name != new_name:
                    self.renames[old_name] = new_name

                new_names.append(
                    name.with_changes(
                        name=cst.parse_expression(
                            new_name
                        )
                    )
                )

            else:
                new_names.append(name)

        return updated_node.with_changes(
            module=cst.parse_expression(
                new_module
            ),
            names=new_names
        )

    def _get_module_name(self, node):

        if node is None:
            return None

        if isinstance(node, cst.Name):
            return node.value

        if isinstance(node, cst.Attribute):
            left = self._get_module_name(node.value)

            if left is None:
                return None

            return f"{left}.{node.attr.value}"

        return None

    def _get_name(self, node):

        if isinstance(node, cst.Name):
            return node.value

        if isinstance(node, cst.Attribute):
            return self._get_module_name(node)

        return ""


class ReferenceMigrationTransformer(cst.CSTTransformer):

    def __init__(self, renames: dict):
        self.renames = renames

    def leave_Name(
        self,
        original_node: cst.Name,
        updated_node: cst.Name
    ):

        if original_node.value in self.renames:

            return updated_node.with_changes(
                value=self.renames[
                    original_node.value
                ]
            )

        return updated_node


class MigrationEngine:

    def migrate(
        self,
        source_code: str,
        migration_map: dict
    ) -> str:

        tree = cst.parse_module(
            source_code
        )

        # -----------------------------------------
        # Step 1: Migrate imports
        # -----------------------------------------

        import_transformer = (
            ImportMigrationTransformer(
                migration_map
            )
        )

        tree = tree.visit(
            import_transformer
        )

        # -----------------------------------------
        # Step 2: Migrate references
        # -----------------------------------------

        reference_transformer = (
            ReferenceMigrationTransformer(
                import_transformer.renames
            )
        )

        tree = tree.visit(
            reference_transformer
        )

        return tree.code
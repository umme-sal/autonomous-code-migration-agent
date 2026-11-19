import ast
from agent2.code_parser import CodeParser
from agent2.code_analyzer import CodeAnalyzer
from agent2.knowledge_retriever import MigrationKnowledgeRetriever
from agent2.migration_advisor import MigrationAdvisor
from agent2.migration_planner import MigrationPlanner
from agent2.migration_engine import MigrationEngine
from agent1.rule_store import RuleStore


class CodeMigrationAgent:

    def __init__(self):

        self.parser = CodeParser()

        self.knowledge_retriever = MigrationKnowledgeRetriever()

        self.migration_advisor = MigrationAdvisor()

        self.migration_planner = MigrationPlanner()

        self.migration_engine = MigrationEngine()

        # ==========================================
        # LOAD LEGACY RULES
        # ==========================================

        self.legacy_rule_store = RuleStore()

        self.legacy_rule_store.load(
            "vector_store/migration_rules.json"
        )

        self.legacy_rules = (
            self.legacy_rule_store.get_rules()
        )

        # ==========================================
        # LOAD ADVANCED RULES
        # ==========================================

        self.advanced_rule_store = RuleStore()

        self.advanced_rule_store.load(
            "vector_store/advanced_migration_rules.json"
        )

        self.advanced_rules = (
            self.advanced_rule_store.get_rules()
        )

        print(
            f"Loaded {len(self.legacy_rules)} legacy rules."
        )

        print(
            f"Loaded {len(self.advanced_rules)} advanced rules."
        )

    # ==================================================
    # 1. LEGACY IMPORT MIGRATION
    # ==================================================

    def migrate_imports(self, source_code: str) -> str:

        tree = self.parser.parse(source_code)

        analyzer = CodeAnalyzer(
            migration_rules=self.legacy_rules
        )

        tree.visit(analyzer)

        migration_maps = []

        for candidate in analyzer.migration_candidates:

            if candidate["type"] != "import":
                continue

            results = (
                self.knowledge_retriever
                .retrieve_for_candidate(candidate)
            )

            if not results:
                continue

            result = (
                self.migration_advisor
                .create_migration_map(
                    source_code=source_code,
                    candidate=candidate,
                    documentation=results
                )
            )

            print("\nLEGACY MIGRATION ADVISOR")
            print(result)

            if result.get("migration_required"):

                migration_maps.append(
                    result["migration_map"]
                )

        migrated_code = source_code

        for migration_map in migration_maps:

            migrated_code = (
                self.migration_engine.migrate(
                    migrated_code,
                    migration_map
                )
            )

        return migrated_code

    # ==================================================
    # 2. SELECT RELEVANT ADVANCED RULES
    # ==================================================

    
    
    def select_relevant_rules(self, source_code: str):

        relevant_rules = []

        try:
            tree = ast.parse(source_code)
        except SyntaxError:
            print("Could not parse source code for rule selection.")
            return relevant_rules

        # Collect function definitions
        function_defs = {
            node.name: node
            for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }

        # R18: Detect synchronous functions containing client.get()
        r18_matched_functions = set()

        for name, function in function_defs.items():

            if isinstance(function, ast.AsyncFunctionDef):
                continue

            for node in ast.walk(function):

                if isinstance(node, ast.Call):
                    if (
                        isinstance(node.func, ast.Attribute)
                        and node.func.attr == "get"
                    ):
                        r18_matched_functions.add(name)
                        break

        # R19: Find functions that call other project functions
        function_callers = set()

        for name, function in function_defs.items():

            for node in ast.walk(function):

                if (
                    isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Name)
                    and node.func.id in function_defs
                ):
                    function_callers.add(name)

        for rule in self.advanced_rules:

            rule_id = rule.get("rule_id")
            matched = False

            # R13: Add stream=True
            if rule_id == "R13":
                matched = ".generate(" in source_code

            # R14: Replace response_format text with json
            elif rule_id == "R14":
                matched = (
                    "client.generate(" in source_code
                    and 'response_format="text"' in source_code
                )

            # R15: Rename run to invoke
            elif rule_id == "R15":
                matched = ".run(" in source_code

            # R17: Prompt template-specific run rename
            elif rule_id == "R17":
                matched = (
                    "prompt_template" in source_code
                    and ".run(" in source_code
                )

            # R18: Convert synchronous function to async
            elif rule_id == "R18":
                matched = bool(r18_matched_functions)

            # R19: Propagate async changes to callers
            elif rule_id == "R19":
                matched = (
                    bool(r18_matched_functions)
                    and bool(function_callers)
                )

            # Unsupported rules
            elif rule_id in {"R07", "R08"}:
                matched = False

            if matched:
                relevant_rules.append(rule)

        return relevant_rules



    # ==================================================
    # 3. ADVANCED STRUCTURED EDIT-PLAN MIGRATION
    # ==================================================

    def migrate_advanced(self, source_code: str) -> str:

        relevant_rules = self.select_relevant_rules(
            source_code
        )

        print("\n" + "=" * 70)
        print("ADVANCED RULE SELECTION")
        print("=" * 70)

        if not relevant_rules:

            print("No matching advanced migration rules.")

            return source_code

        for rule in relevant_rules:

            print(
                rule.get("rule_id"),
                "-",
                rule.get("description")
            )

        # --------------------------------------
        # Generate structured edit plan
        # --------------------------------------

        edit_plan = (
            self.migration_planner.generate_edit_plan(
                source_code=source_code,
                retrieved_docs=[],
                migration_rules=relevant_rules
            )
        )

        print("\n" + "=" * 70)
        print("ADVANCED MIGRATION EDIT PLAN")
        print("=" * 70)

        print(edit_plan)

        # --------------------------------------
        # Report manual review
        # --------------------------------------

        manual_review = edit_plan.get(
            "manual_review",
            []
        )

        if manual_review:

            print("\nMANUAL REVIEW REQUIRED:")

            for item in manual_review:

                print(item)

        # --------------------------------------
        # Apply validated edit plan
        # --------------------------------------

        migrated_code = (
            self.migration_engine.migrate_with_edit_plan(
                source_code,
                edit_plan
            )
        )

        return migrated_code

    # ==================================================
    # 4. COMPLETE MIGRATION PIPELINE
    # ==================================================

    def migrate_code(self, source_code: str) -> str:

        print("\nStarting legacy import migration...")

        migrated_code = self.migrate_imports(
            source_code
        )

        print("\nStarting advanced migration...")

        migrated_code = self.migrate_advanced(
            migrated_code
        )

        return migrated_code

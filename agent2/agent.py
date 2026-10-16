from agent2.code_parser import CodeParser
from agent2.code_analyzer import CodeAnalyzer
from agent2.knowledge_retriever import MigrationKnowledgeRetriever
from agent2.migration_advisor import MigrationAdvisor
from agent2.migration_engine import MigrationEngine
from agent1.rule_store import RuleStore


class CodeMigrationAgent:

    def __init__(self):

        self.parser = CodeParser()

        self.knowledge_retriever = (
            MigrationKnowledgeRetriever()
        )

        self.migration_advisor = MigrationAdvisor()

        self.migration_engine = MigrationEngine()

        # Load migration rules extracted from documentation
        self.rule_store = RuleStore()

        self.rule_store.load(
            "vector_store/migration_rules.json"
        )

        self.migration_rules = (
            self.rule_store.get_rules()
        )

        print(
            f"Loaded {len(self.migration_rules)} migration rules."
        )

    # --------------------------------------------------
    # Step 1: Analyze source code
    # --------------------------------------------------

    def analyze(self, source_code: str):

        tree = self.parser.parse(source_code)

        analyzer = CodeAnalyzer(
            migration_rules=self.migration_rules
        )

        tree.visit(analyzer)

        return analyzer

    # --------------------------------------------------
    # Step 2: Retrieve knowledge from Agent 1
    # --------------------------------------------------

    def retrieve_knowledge(self, source_code: str):

        analyzer = self.analyze(source_code)

        knowledge = []

        for candidate in analyzer.migration_candidates:

            results = (
                self.knowledge_retriever
                .retrieve_for_candidate(
                    candidate
                )
            )

            knowledge.append({
                "candidate": candidate,
                "results": results
            })

        return knowledge

    # --------------------------------------------------
    # Step 3: Generate migration maps using LLM
    # --------------------------------------------------

    def generate_migration_maps(
        self,
        source_code: str
    ):

        knowledge = self.retrieve_knowledge(
            source_code
        )

        migration_maps = []

        for item in knowledge:

            candidate = item["candidate"]

            if candidate["type"] != "import":
                continue
            results = item["results"]

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

            print("\n" + "=" * 70)
            print("MIGRATION ADVISOR")
            print("=" * 70)

            print(result)

            if result.get("migration_required"):

                migration_maps.append(
                    result["migration_map"]
                )

        return migration_maps

    # --------------------------------------------------
    # Step 4: Apply migrations
    # --------------------------------------------------

    def migrate_code(
        self,
        source_code: str
    ):

        migration_maps = (
            self.generate_migration_maps(
                source_code
            )
        )

        migrated_code = source_code

        for migration_map in migration_maps:

            migrated_code = (
                self.migration_engine
                .migrate(
                    migrated_code,
                    migration_map
                )
            )

        return migrated_code
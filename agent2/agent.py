from agent2.code_parser import CodeParser
from agent2.code_analyzer import CodeAnalyzer
from agent2.knowledge_retriever import MigrationKnowledgeRetriever
from agent2.migration_advisor import MigrationAdvisor


class CodeMigrationAgent:

    def __init__(self):

        self.parser = CodeParser()

        self.knowledge_retriever = (
            MigrationKnowledgeRetriever()
        )

        self.migration_advisor = MigrationAdvisor()

    def analyze(self, source_code: str):

        tree = self.parser.parse(source_code)

        analyzer = CodeAnalyzer()

        tree.visit(analyzer)

        return analyzer

    def retrieve_knowledge(self, source_code: str):

        analyzer = self.analyze(source_code)

        knowledge = []

        for candidate in analyzer.migration_candidates:

            results = (
                self.knowledge_retriever
                .retrieve_for_candidate(candidate)
            )

            knowledge.append({
                "candidate": candidate,
                "results": results
            })

        return knowledge

    def generate_migration_map(
        self,
        source_code: str
    ):

        knowledge = self.retrieve_knowledge(
            source_code
        )

        migration_maps = []

        for item in knowledge:

            candidate = item["candidate"]
            results = item["results"]

            if not results:
                continue

            migration_map = (
                self.migration_advisor
                .create_migration_map(
                    source_code=source_code,
                    candidate=candidate,
                    documentation=results
                )
            )

            migration_maps.append(
                migration_map
            )

        return migration_maps
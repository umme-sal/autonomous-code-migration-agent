from agent1.agent import MigrationKnowledgeAgent


class MigrationKnowledgeRetriever:

    def __init__(self):
        self.knowledge_agent = MigrationKnowledgeAgent(
            similarity_threshold=0.30
        )

    def retrieve_for_candidate(self, candidate: dict) -> list[dict]:

        query = self._build_query(candidate)

        print("\nSearch Query:")
        print(query)

        return self.knowledge_agent.search(query)

    def _build_query(self, candidate: dict) -> str:

        code = candidate["code"]
        candidate_type = candidate["type"]

        return (
            f"Legacy Python migration modernization.\n"
            f"Migration type: {candidate_type}\n"
            f"Source code: {code}\n"
            f"How should this legacy code be migrated "
            f"to a modern implementation?"
        )
from agent1.agent import MigrationKnowledgeAgent


class MigrationKnowledgeRetriever:

    def __init__(self):

        self.knowledge_agent = MigrationKnowledgeAgent(
            similarity_threshold=0.30
        )

    def retrieve_for_candidate(
        self,
        candidate: dict
    ) -> list[dict]:

        query = self._build_query(candidate)

        print("\n" + "=" * 70)
        print("AGENT 2 → AGENT 1")
        print("=" * 70)

        print("\nSearch Query:")
        print(query)

        results = self.knowledge_agent.search(query)

        print("\nRetrieved Documentation:")

        if not results:
            print("No relevant documentation found.")

        for result in results:

            print("\nScore:", result["score"])
            print("Source:", result["source"])
            print("Text:")
            print(result["text"])

        return results

    def _build_query(
        self,
        candidate: dict
    ) -> str:

        rule = candidate["rule"]

        symbol = rule.get("source", "")
        source_module = rule.get("source_module", "")
        target = rule.get("target", "")
        target_module = rule.get("target_module", "")

        code = candidate["code"]

        return (
            "Python code migration.\n\n"
            f"Legacy code:\n{code}\n\n"
            f"Legacy symbol: {symbol}\n"
            f"Legacy module: {source_module}\n\n"
            f"Target symbol: {target}\n"
            f"Target module: {target_module}\n\n"
            "Find the migration documentation that explains "
            "how this legacy API should be migrated."
        )
from agent1.document_loader import load_document
from agent1.rule_extractor import MigrationRuleExtractor
from agent1.rule_store import RuleStore


def main():

    document_path = (
        "documents/migration_docs/"
        "langchain_langgraph_migration_guide.pdf"
    )

    rules_file = "vector_store/migration_rules.json"

    print("\nReading migration document...")

    document_text = load_document(document_path)

    print("Extracting migration rules...")

    extractor = MigrationRuleExtractor()
    result = extractor.extract_rules(document_text)

    rules = result.get("rules", [])

    print(f"Rules extracted: {len(rules)}")

    rule_store = RuleStore()
    rule_store.add_rules(rules)
    rule_store.save(rules_file)

    print(f"Rules saved to: {rules_file}")


if __name__ == "__main__":
    main()
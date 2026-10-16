import json

from agent1.document_loader import load_document
from agent1.rule_extractor import MigrationRuleExtractor


def main():

    document_path = (
        "documents/migration_docs/"
        "langchain_langgraph_migration_guide.pdf"
    )

    document_text = load_document(document_path)

    extractor = MigrationRuleExtractor()

    result = extractor.extract_rules(document_text)

    print("\n" + "=" * 70)
    print("EXTRACTED MIGRATION RULES")
    print("=" * 70)

    print(
        json.dumps(
            result,
            indent=4,
            ensure_ascii=False
        )
    )

    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
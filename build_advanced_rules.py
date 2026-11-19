
import json
from pathlib import Path

from agent1.document_loader import load_document
from agent1.rule_extractor import MigrationRuleExtractor


def main():

    document_path = Path(
        "documents/migration_docs/migration_rules.pdf"
    )

    output_path = Path(
        "vector_store/advanced_migration_rules.json"
    )

    print("\nReading advanced migration guide...")

    if not document_path.exists():
        raise FileNotFoundError(
            f"Migration guide not found: {document_path}"
        )

    document_text = load_document(str(document_path))

    print("Extracting migration rules...")

    extractor = MigrationRuleExtractor()
    result = extractor.extract_rules(document_text)

    rules = result.get("rules", [])

    print(f"\nRules extracted: {len(rules)}")

    if len(rules) != 30:
        raise ValueError(
            f"Expected 30 rules, but extracted {len(rules)}. "
            "Check the extraction output before proceeding."
        )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(
            {"rules": rules},
            file,
            indent=2,
            ensure_ascii=False
        )

    print(f"\nRules saved to: {output_path}")

    print("\nRule IDs:")
    for rule in rules:
        print(rule.get("rule_id"))


if __name__ == "__main__":
    main()

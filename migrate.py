import sys
from pathlib import Path

from agent2.agent import CodeMigrationAgent
from agent2.validator import MigrationValidator
from agent2.diff_generator import MigrationDiffGenerator


def main():

    if len(sys.argv) != 3:
        print("Usage: uv run python migrate.py <input_file.py> <output_file.py>")
        sys.exit(1)

    input_file = Path(sys.argv[1])
    output_file = Path(sys.argv[2])

    if not input_file.exists():
        print(f"Error: File not found: {input_file}")
        sys.exit(1)

    if input_file.suffix != ".py":
        print("Error: Input must be a Python file.")
        sys.exit(1)

    print("=" * 70)
    print("AUTONOMOUS CODE MIGRATION AGENT")
    print("=" * 70)

    print(f"Input : {input_file}")
    print(f"Output: {output_file}")

    # Step 1: Read original code
    original_code = input_file.read_text(encoding="utf-8")

    # Step 2: Perform migration
    agent = CodeMigrationAgent()

    print("\nStarting migration...")
    migrated_code = agent.migrate_code(original_code)

    # Step 3: Validate migrated code
    print("\nValidating migrated code...")

    validator = MigrationValidator()
    validation_result = validator.validate_syntax(migrated_code)

    if not validation_result["valid"]:

        error = validation_result["error"]

        print("\n" + "=" * 70)
        print("MIGRATION VALIDATION FAILED")
        print("=" * 70)

        print(f"Error  : {error['message']}")
        print(f"Line   : {error['line']}")
        print(f"Column : {error['column']}")

        print("\nOutput file was NOT saved.")
        sys.exit(1)

    # Step 4: Generate diff
    diff_generator = MigrationDiffGenerator()
    diff = diff_generator.generate_diff(
        original_code,
        migrated_code
    )

    # Step 5: Save migrated file
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(migrated_code, encoding="utf-8")

    # Step 6: Display results
    print("\n" + "=" * 70)
    print("MIGRATION SUCCESSFUL")
    print("=" * 70)

    print("Syntax validation: PASSED")
    print(f"Migrated file: {output_file}")

    print("\n" + "=" * 70)
    print("MIGRATION DIFF")
    print("=" * 70)

    if diff:
        print(diff)
    else:
        print("No changes detected.")


if __name__ == "__main__":
    main()
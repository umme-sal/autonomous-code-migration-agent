import sys
from pathlib import Path

from agent2.agent import CodeMigrationAgent


def main():

    if len(sys.argv) != 3:
        print(
            "Usage: python migrate.py "
            "<input_file.py> <output_file.py>"
        )
        sys.exit(1)

    input_file = Path(sys.argv[1])
    output_file = Path(sys.argv[2])

    if not input_file.exists():
        print(f"Error: File not found: {input_file}")
        sys.exit(1)

    if input_file.suffix != ".py":
        print("Error: Input file must be a Python file.")
        sys.exit(1)

    print("=" * 70)
    print("AUTONOMOUS CODE MIGRATION AGENT")
    print("=" * 70)

    print(f"\nInput : {input_file}")
    print(f"Output: {output_file}")

    # Read source code
    source_code = input_file.read_text(
        encoding="utf-8"
    )

    # Create migration agent
    agent = CodeMigrationAgent()

    # Perform migration
    migrated_code = agent.migrate_code(
        source_code
    )

    # Write migrated code
    output_file.write_text(
        migrated_code,
        encoding="utf-8"
    )

    print("\n" + "=" * 70)
    print("MIGRATION COMPLETE")
    print("=" * 70)

    print(f"\nMigrated file created:")
    print(output_file)


if __name__ == "__main__":
    main()
    
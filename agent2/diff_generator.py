import difflib


class MigrationDiffGenerator:

    def generate_diff(self, original_code: str, migrated_code: str) -> str:

        original_lines = original_code.splitlines(keepends=True)
        migrated_lines = migrated_code.splitlines(keepends=True)

        diff = difflib.unified_diff(
            original_lines,
            migrated_lines,
            fromfile="original.py",
            tofile="migrated.py",
            lineterm="\n"
        )

        return "".join(diff)
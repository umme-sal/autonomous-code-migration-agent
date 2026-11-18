
import ast


class MigrationValidator:

    def validate_syntax(self, source_code: str) -> dict:

        try:
            ast.parse(source_code)

            return {
                "valid": True,
                "error": None
            }

        except SyntaxError as error:

            return {
                "valid": False,
                "error": {
                    "message": error.msg,
                    "line": error.lineno,
                    "column": error.offset
                }
            }

import libcst as cst


class CodeParser:

    def parse(self, source_code: str) -> cst.Module:
        return cst.parse_module(source_code)
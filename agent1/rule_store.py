import json
from pathlib import Path


class RuleStore:

    def __init__(self):
        self.rules = []

    def add_rules(self, rules: list[dict]):
        self.rules.extend(rules)

    def get_rules(self) -> list[dict]:
        return self.rules

    def save(self, file_path: str):
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w", encoding="utf-8") as file:
            json.dump(
                {"rules": self.rules},
                file,
                indent=4,
                ensure_ascii=False
            )

    def load(self, file_path: str):
        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)

        self.rules = data.get("rules", [])
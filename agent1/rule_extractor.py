import json
import os

from dotenv import load_dotenv
from groq import Groq


load_dotenv()


class MigrationRuleExtractor:

    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")

        if not api_key:
            raise ValueError("GROQ_API_KEY is not set.")

        self.client = Groq(api_key=api_key)
        self.model = "openai/gpt-oss-120b"

    def extract_rules(self, document_text: str) -> dict:

        prompt = f"""
You are a Python code migration knowledge extractor.

Analyze the migration documentation below and extract
all explicit code migration rules.

MIGRATION DOCUMENT:
{document_text}

Extract rules such as:

- module/package renames
- class renames
- function renames
- method renames
- API changes
- import changes
- attribute changes
- syntax changes

Only extract rules that are explicitly supported by
the documentation.

Do NOT invent migration rules.

Return ONLY valid JSON using exactly this structure:

{{
    "rules": [
        {{
            "type": "module",
            "source": "old_module",
            "target": "new_module"
        }},
        {{
            "type": "symbol",
            "source": "OldClass",
            "target": "NewClass",
            "source_module": "old_module",
            "target_module": "new_module"
        }}
    ]
}}

If no migration rules can be identified, return:

{{
    "rules": []
}}
"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0
        )

        content = response.choices[0].message.content

        return json.loads(content)
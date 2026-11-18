
import json
import os

from dotenv import load_dotenv
from groq import Groq


load_dotenv()


class MigrationPlanner:

    def __init__(self):

        api_key = os.getenv("GROQ_API_KEY")

        if not api_key:
            raise ValueError("GROQ_API_KEY is not set.")

        self.client = Groq(api_key=api_key)
        self.model = "openai/gpt-oss-120b"

    def generate_edit_plan(
        self,
        source_code: str,
        retrieved_docs: list[dict],
        migration_rules: list[dict]
    ) -> dict:

        # No evidence means no function-call migration.
        if not retrieved_docs or not migration_rules:
            return {
                "migration_required": False,
                "targets": []
            }

        documentation = "\n\n".join(
            item["text"] for item in retrieved_docs
        )

        rules = json.dumps(
            migration_rules,
            indent=4
        )

        prompt = f"""
You are an expert Python code migration planner.

Analyze the source code and generate a structured edit plan.

STRICT RULES:

1. Use ONLY explicitly provided migration rules.
2. Never invent a migration.
3. Use documentation as supporting evidence.
4. Do not rewrite the complete source code.
5. Every target_code must exactly match a function call
   in the original source code.
6. Only generate edits supported by the documentation.
7. If no supported function-call migration exists,
   return migration_required=false and targets=[].

SUPPORTED EDIT TARGETS:
- method_name
- arguments

SUPPORTED OPERATION:
- replace

For method_name:

{{
    "target": "method_name",
    "operation": "replace",
    "value": {{
        "type": "identifier",
        "name": "new_method"
    }}
}}

For arguments:

{{
    "target": "arguments",
    "operation": "replace",
    "value": [
        {{
            "type": "positional_argument",
            "value": {{
                "type": "identifier",
                "name": "prompt"
            }}
        }}
    ]
}}

SOURCE CODE:
{source_code}

MIGRATION RULES:
{rules}

SUPPORTING DOCUMENTATION:
{documentation}

Return ONLY valid JSON.

Expected structure:

{{
    "migration_required": true,
    "targets": [
        {{
            "target_code": "exact function call from source",
            "edits": []
        }}
    ]
}}

If no supported migration exists:

{{
    "migration_required": false,
    "targets": []
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

        if not content:
            raise ValueError("The LLM returned an empty response.")

        content = content.strip()

        # Remove Markdown code fences.
        if content.startswith("```"):

            content = content.split("\n", 1)[1]
            content = content.rsplit("```", 1)[0].strip()

        try:
            edit_plan = json.loads(content)

        except json.JSONDecodeError as error:
            raise ValueError(
                f"LLM returned invalid JSON: {content}"
            ) from error

        if not isinstance(edit_plan, dict):
            raise ValueError("Edit plan must be a JSON object.")

        if not isinstance(
            edit_plan.get("migration_required"), bool
        ):
            raise ValueError("migration_required must be boolean.")

        if not isinstance(edit_plan.get("targets"), list):
            raise ValueError("targets must be a list.")

        return edit_plan

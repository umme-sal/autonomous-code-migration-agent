
import json
import os

from dotenv import load_dotenv
from groq import Groq


load_dotenv()


class MigrationAdvisor:

    def __init__(self):

        api_key = os.getenv("GROQ_API_KEY")

        if not api_key:
            raise ValueError(
                "GROQ_API_KEY is not set."
            )

        self.client = Groq(
            api_key=api_key
        )

        self.model = "openai/gpt-oss-120b"

    # --------------------------------------------------
    # EXISTING: IMPORT / MODULE MIGRATION
    # --------------------------------------------------

    def create_migration_map(
        self,
        source_code: str,
        candidate: dict,
        documentation: list[dict]
    ) -> dict:

        documentation_text = "\n\n".join(
            result["text"]
            for result in documentation
        )

        prompt = f"""
You are a Python code migration expert.

Analyze the source code and the retrieved migration documentation.

SOURCE CODE:
{source_code}

MIGRATION CANDIDATE:
{candidate["code"]}

RETRIEVED DOCUMENTATION:
{documentation_text}

Determine whether the migration candidate requires
a code transformation.

Return ONLY valid JSON.

Use this structure:

{{
    "migration_required": true,
    "migration_map": {{
        "old_module": {{
            "module": "new_module",
            "names": {{
                "OldName": "NewName"
            }}
        }}
    }}
}}

If the documentation does not provide enough information,
return:

{{
    "migration_required": false,
    "migration_map": {{}}
}}

Do not invent migration rules that are not supported
by the documentation.
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

    # --------------------------------------------------
    # NEW: GENERIC STRUCTURAL EDIT PLAN
    # --------------------------------------------------

    def create_edit_plan(
        self,
        source_code: str,
        candidate: dict,
        documentation: list[dict]
    ) -> dict:

        documentation_text = "\n\n".join(
            result["text"]
            for result in documentation
        )

        prompt = f"""
You are a software migration analysis expert.

Analyze the source code, migration candidate,
and retrieved migration documentation.

Your task is to recommend structural code edits
that can be applied by a Concrete Syntax Tree (CST)
transformation engine.

IMPORTANT RULES:

1. Do NOT generate replacement Python source code.
2. Do NOT rewrite the entire function.
3. Recommend only changes supported by the documentation.
4. Do not invent APIs or migration requirements.
5. Preserve the original program's behavior as much as
   the migration documentation allows.
6. Describe changes using the JSON edit-plan format.
7. If the migration cannot be confidently determined,
   return migration_required=false.
8. target_code must refer to code present in the source.
9. Expressions must use the expression representation
   defined below.
10. Return ONLY valid JSON. No Markdown fences.

SOURCE CODE:
{source_code}

MIGRATION CANDIDATE:
{candidate["code"]}

RETRIEVED DOCUMENTATION:
{documentation_text}

--------------------------------------------------
OUTPUT FORMAT
--------------------------------------------------

Return a JSON object using this structure:

{{
    "migration_required": true,
    "reason": "Brief explanation of the migration",
    "targets": [
        {{
            "target_code": "client.run(prompt)",
            "edits": [
                {{
                    "target": "method_name",
                    "operation": "replace",
                    "value": {{
                        "type": "identifier",
                        "name": "invoke"
                    }}
                }},
                {{
                    "target": "arguments",
                    "operation": "replace",
                    "value": [
                        {{
                            "type": "keyword_argument",
                            "name": "input",
                            "value": {{
                                "type": "identifier",
                                "name": "prompt"
                            }}
                        }}
                    ]
                }}
            ]
        }}
    ]
}}

--------------------------------------------------
SUPPORTED EXPRESSION REPRESENTATIONS
--------------------------------------------------

Identifier:
{{
    "type": "identifier",
    "name": "variable_name"
}}

String:
{{
    "type": "string",
    "value": "hello"
}}

Number:
{{
    "type": "number",
    "value": 10
}}

Boolean:
{{
    "type": "boolean",
    "value": true
}}

None:
{{
    "type": "none"
}}

Dictionary:
{{
    "type": "dictionary",
    "entries": [
        {{
            "key": "input",
            "value": {{
                "type": "identifier",
                "name": "prompt"
            }}
        }}
    ]
}}

List:
{{
    "type": "list",
    "elements": [
        {{
            "type": "identifier",
            "name": "prompt"
        }}
    ]
}}

Attribute:
{{
    "type": "attribute",
    "value": {{
        "type": "identifier",
        "name": "client"
    }},
    "attr": "invoke"
}}

Call:
{{
    "type": "call",
    "function": {{
        "type": "attribute",
        "value": {{
            "type": "identifier",
            "name": "client"
        }},
        "attr": "invoke"
    }},
    "arguments": []
}}

--------------------------------------------------
EDIT TARGETS
--------------------------------------------------

The target field identifies which part of the CST node
should be modified.

Examples:

"method_name"
"arguments"
"function_name"
"attribute"
"expression"

--------------------------------------------------
EDIT OPERATIONS
--------------------------------------------------

"replace"

The replace operation replaces the selected structural
component with the provided expression representation.

Do not propose operations outside the defined format.

--------------------------------------------------
NO MIGRATION CASE
--------------------------------------------------

If no migration is required, or documentation does not
sufficiently support a transformation, return:

{{
    "migration_required": false,
    "reason": "Explanation",
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

        content = response.choices[0].message.content.strip()

        # Remove Markdown code fences if present
        if content.startswith("```"):
            lines = content.splitlines()

            if lines[0].startswith("```"):
                lines = lines[1:]

            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]

            content = "\n".join(lines).strip()

        return json.loads(content)

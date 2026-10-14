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
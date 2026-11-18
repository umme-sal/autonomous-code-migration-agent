
import os
from dotenv import load_dotenv
from groq import Groq


class CodeRewriter:

    def __init__(self):
        load_dotenv()

        self.client = Groq(
            api_key=os.getenv("GROQ_API_KEY")
        )

        self.model = "openai/gpt-oss-120b"

    def rewrite(self, code, migration_rules, documentation=""):

        prompt = f"""
You are an expert software migration engineer.

Your task is to migrate the provided code according to the
migration rules and supporting documentation.

IMPORTANT RULES:
1. Rewrite the code to comply with the migration rules.
2. Preserve the original functionality.
3. Do not remove unrelated logic.
4. Do not invent APIs that are not supported by the rules
   or documentation.
5. Preserve variable names whenever possible.
6. Return ONLY the rewritten code.
7. Do not include explanations or Markdown code fences.

CODE TO MIGRATE:
{code}

MIGRATION RULES:
{migration_rules}

SUPPORTING DOCUMENTATION:
{documentation}
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

        rewritten_code = response.choices[0].message.content

        return self._clean_response(rewritten_code)

    def _clean_response(self, code):

        code = code.strip()

        # Remove Markdown code fences if the LLM returns them
        if code.startswith("```"):
            lines = code.splitlines()

            if lines[0].startswith("```"):
                lines = lines[1:]

            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]

            code = "\n".join(lines)

        return code.strip()

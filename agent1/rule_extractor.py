
import hashlib
import json
import os
import re
import time
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq, RateLimitError


load_dotenv()


class MigrationRuleExtractor:

    MODEL = "openai/gpt-oss-120b"

    EXPECTED_RULE_COUNT = 30
    BATCH_SIZE = 2
    SCHEMA_VERSION = 3
    PROMPT_VERSION = "operations-v1"

    CHECKPOINT_PATH = Path(
        "vector_store/rule_extraction_checkpoint_v3.json"
    )

    REQUIRED_FIELDS = [
        "rule_id",
        "category",
        "transformation_type",
        "description",
        "element_type",
        "source",
        "target",
        "source_module",
        "target_module",
        "targets",
        "operations",
        "preconditions",
        "required_changes",
        "safety_conditions",
        "examples",
        "source_excerpt"
    ]

    TARGET_FIELDS = [
        "element_type",
        "old_name",
        "new_name",
        "source_module",
        "target_module"
    ]

    def __init__(self):

        api_key = os.getenv("GROQ_API_KEY")

        if not api_key:
            raise ValueError(
                "GROQ_API_KEY is missing. "
                "Add it to your .env file."
            )

        self.client = Groq(api_key=api_key)
        self.model = self.MODEL

        self.checkpoint_path = self.CHECKPOINT_PATH

    # ==================================================
    # 1. NORMALIZE DOCUMENT TEXT
    # ==================================================

    def normalize_text(self, text: str) -> str:

        if not isinstance(text, str):
            raise TypeError("Document text must be a string.")

        return re.sub(r"\s+", " ", text).strip()

    # ==================================================
    # 2. SPLIT DOCUMENT INTO RULES
    # ==================================================

    def split_rules(self, document_text: str) -> list[str]:

        text = self.normalize_text(document_text)

        pattern = r"\bRule\s+(\d{1,2})\s*:"

        matches = list(
            re.finditer(pattern, text, re.IGNORECASE)
        )

        if not matches:
            raise ValueError(
                "No rule headings found in the document."
            )

        rule_sections = []

        for index, match in enumerate(matches):

            start = match.start()

            if index + 1 < len(matches):
                end = matches[index + 1].start()
            else:
                end = len(text)

            rule_sections.append(text[start:end].strip())

        if len(rule_sections) != self.EXPECTED_RULE_COUNT:

            raise ValueError(
                f"Expected {self.EXPECTED_RULE_COUNT} rules, "
                f"but found {len(rule_sections)}."
            )

        print("\n===== RULE SPLITTING SUMMARY =====")
        print("Total rule sections found:", len(rule_sections))

        return rule_sections

    # ==================================================
    # 3. GET RULE ID FROM DOCUMENT SECTION
    # ==================================================

    def get_rule_id(self, rule_text: str) -> str:

        match = re.search(
            r"\bRule\s+(\d{1,2})\s*:",
            rule_text,
            re.IGNORECASE
        )

        if not match:
            raise ValueError(
                "Could not identify rule number in section."
            )

        return f"R{int(match.group(1)):02d}"

    # ==================================================
    # 4. CREATE BATCHES
    # ==================================================

    def create_batches(
        self,
        rule_sections: list[str]
    ) -> list[list[str]]:

        return [
            rule_sections[i:i + self.BATCH_SIZE]
            for i in range(
                0,
                len(rule_sections),
                self.BATCH_SIZE
            )
        ]

    # ==================================================
    # 5. BUILD EXTRACTION PROMPT
    # ==================================================

    def build_prompt(self, batch_text: str) -> str:

        return f"""
You are an expert software migration knowledge extractor.

Your task is to convert migration documentation into
structured, machine-readable migration rules.

Extract ONLY the rules explicitly supported by the
documentation below.

DOCUMENTATION:
{batch_text}

==================================================
IMPORTANT EXTRACTION PRINCIPLES
==================================================

1. Extract every rule in the supplied documentation.
2. Preserve the original rule number.
3. Do not invent migration behavior.
4. Do not omit explicit transformation requirements.
5. Preserve all safety conditions.
6. Preserve all preconditions.
7. Use the Before and After examples to identify
   concrete code transformations.
8. Do not merge separate rules.
9. Do not create additional rules.
10. Do not leave category or transformation_type empty.
11. Provide a meaningful, concise description.
12. If a detail is not specified, use an empty string
    or empty list rather than guessing.
13. Copy a relevant source_excerpt from the supplied
    documentation. Do not invent quotations.
14. Keep examples faithful to the documentation.
15. Do not treat an example as permission to invent
    behavior beyond what it demonstrates.

==================================================
CATEGORIES
==================================================

Choose the most appropriate category:

- import_migration
- function_definition
- function_call
- method_migration
- async_migration
- iteration_migration
- class_migration
- decorator_migration
- constructor_migration
- type_annotation
- configuration_migration
- enum_migration
- exception_migration

==================================================
TRANSFORMATION TYPES
==================================================

Choose a concise transformation type that describes
the actual change.

Examples:

- relocate_import
- rename_imported_symbol
- manual_review_required
- rename_function
- rename_parameter
- add_required_parameter
- remove_deprecated_parameter
- reorder_parameters
- change_default_value
- rename_keyword_argument
- positional_to_keyword_argument
- add_keyword_argument
- replace_argument_value
- rename_method
- replace_method
- convert_to_async
- propagate_async
- replace_sync_iteration
- rename_class
- change_base_class
- replace_decorator
- replace_constructor
- change_return_type
- rename_configuration_key
- restructure_configuration
- replace_constant_with_enum
- rename_exception_class
- modify_exception_handling_structure

Do not use an empty transformation_type.

==================================================
TARGETS
==================================================

The targets field must be a list.

Each target must contain:

- element_type
- old_name
- new_name
- source_module
- target_module

Create a separate target object for each independent
mapping.

For example, if two symbols move to different modules,
create two target objects.

Do not combine them into one ambiguous mapping.

For rules that do not have a concrete name mapping,
use an empty targets list if appropriate.

==================================================
OPERATIONS
==================================================

This is especially important.

The operations field must be a list of structured
instructions describing exactly what code transformation
is required.

Each operation must be a JSON object.

Use an "operation" field to identify the action.

Other fields should describe the relevant details.

Examples of operation types:

- relocate_import
- rename_symbol
- rename_function
- rename_parameter
- add_parameter
- remove_parameter
- reorder_parameters
- change_default_value
- rename_keyword_argument
- positional_to_keyword
- add_keyword_argument
- replace_argument_value
- rename_method
- restructure_method_call
- wrap_argument
- move_argument
- convert_to_async
- add_await
- propagate_async
- replace_for_with_async_for
- rename_class
- change_base_class
- replace_decorator
- replace_constructor
- change_return_type
- rename_configuration_key
- restructure_configuration
- replace_constant_with_enum
- rename_exception
- modify_exception_handling
- manual_review

Example for a method replacement:

"operations": [
    {{
        "operation": "rename_method",
        "old_value": "predict",
        "new_value": "invoke"
    }},
    {{
        "operation": "wrap_argument",
        "argument": "prompt",
        "wrapper": "input"
    }},
    {{
        "operation": "move_argument",
        "argument": "temperature",
        "destination": "config"
    }}
]

Example for a required parameter:

"operations": [
    {{
        "operation": "add_parameter",
        "function": "request",
        "parameter": "timeout",
        "required_value": 30
    }}
]

Only include required_value when the documentation
explicitly supplies that value.

Example for manual review:

"operations": [
    {{
        "operation": "manual_review",
        "reason": "The required migration information is missing."
    }}
]

Do not use these examples as migration instructions
unless they match the actual documentation.

Every operation must be grounded in the rule text,
its examples, or its explicit transformation requirements.

If the documentation does not provide enough information
to safely create an operation, use manual_review and
explain why.

Do not create vague operations such as "migrate code"
or "update function".

==================================================
REQUIRED CHANGES
==================================================

The required_changes list must explain the actual
changes needed.

Do not leave it empty when the documentation provides
a clear transformation.

For example:

[
    "Rename the method predict to invoke.",
    "Wrap the prompt argument in an input dictionary.",
    "Move temperature into the config dictionary."
]

Keep each instruction specific and actionable.

==================================================
SAFETY CONDITIONS
==================================================

Preserve every explicit safety requirement.

Examples include:

- Never invent a required parameter value.
- Do not add await inside a synchronous function.
- Do not convert unrelated functions to async.
- Do not overwrite existing configuration values.
- Do not guess wildcard import names.
- Do not change exception behavior unless explicitly
  required by the migration rule.
- Require manual review when a safe transformation
  cannot be established.

Do not remove safety conditions just because an example
shows a successful transformation.

==================================================
BACKWARD COMPATIBILITY
==================================================

Also populate these top-level fields:

- element_type
- source
- target
- source_module
- target_module

These fields are retained for the existing Agent 2.

For a single target, populate them from that target
where applicable.

For multiple targets with different mappings, leave
ambiguous top-level fields as empty strings.

For non-import transformations, use these fields
where meaningful, otherwise use empty strings.

Keep all detailed mappings in targets.

==================================================
OUTPUT FORMAT
==================================================

Return ONLY valid JSON.

Use this structure:

{{
    "rules": [
        {{
            "rule_id": "R01",
            "category": "import_migration",
            "transformation_type": "relocate_import",
            "description": "Move ChatModel to its new module.",
            "element_type": "import",
            "source": "ChatModel",
            "target": "ChatModel",
            "source_module": "legacy_sdk.models",
            "target_module": "modern_sdk.models",

            "targets": [
                {{
                    "element_type": "import",
                    "old_name": "ChatModel",
                    "new_name": "ChatModel",
                    "source_module": "legacy_sdk.models",
                    "target_module": "modern_sdk.models"
                }}
            ],

            "operations": [
                {{
                    "operation": "relocate_import",
                    "symbol": "ChatModel",
                    "source_module": "legacy_sdk.models",
                    "target_module": "modern_sdk.models"
                }}
            ],

            "preconditions": [],

            "required_changes": [
                "Move the ChatModel import to modern_sdk.models."
            ],

            "safety_conditions": [],

            "examples": {{
                "before": "from legacy_sdk.models import ChatModel",
                "after": "from modern_sdk.models import ChatModel"
            }},

            "source_excerpt": "Relevant original rule text."
        }}
    ]
}}

Return one object per documented rule.

If no rules are found, return:

{{
    "rules": []
}}
"""

    # ==================================================
    # 6. CALL LLM WITH RETRIES
    # ==================================================

    def call_llm(self, prompt: str) -> str:

        max_retries = 5

        for attempt in range(max_retries):

            try:

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

                choice = response.choices[0]

                print(
                    "Batch finish reason:",
                    choice.finish_reason
                )

                if choice.finish_reason == "length":
                    raise ValueError(
                        "LLM response was truncated. "
                        "Reduce BATCH_SIZE."
                    )

                content = choice.message.content

                if not content:
                    raise ValueError(
                        "LLM returned an empty response."
                    )

                return content.strip()

            except RateLimitError:

                if attempt == max_retries - 1:
                    raise

                wait_time = 10 * (attempt + 1)

                print(
                    f"Rate limit reached. "
                    f"Retrying in {wait_time} seconds..."
                )

                time.sleep(wait_time)

        raise RuntimeError("LLM request failed.")

    # ==================================================
    # 7. PARSE LLM JSON
    # ==================================================

    def parse_response(self, content: str) -> list[dict]:

        content = re.sub(
            r"^```(?:json)?\s*|\s*```$",
            "",
            content.strip(),
            flags=re.IGNORECASE
        )

        try:
            result = json.loads(content)

        except json.JSONDecodeError as error:

            raise ValueError(
                f"Invalid JSON returned by LLM: {error}"
            ) from error

        if not isinstance(result, dict):
            raise ValueError(
                "LLM response must be a JSON object."
            )

        rules = result.get("rules")

        if not isinstance(rules, list):
            raise ValueError(
                "The response must contain a rules list."
            )

        return rules

    # ==================================================
    # 8. NORMALIZE RULE ID
    # ==================================================

    def normalize_rule_id(self, raw_rule_id: str) -> str:

        match = re.search(
            r"(\d+)",
            str(raw_rule_id)
        )

        if not match:
            raise ValueError(
                f"Invalid rule ID: {raw_rule_id}"
            )

        return f"R{int(match.group(1)):02d}"

    # ==================================================
    # 9. VALIDATE ONE RULE
    # ==================================================

    def validate_rule(self, rule: dict):

        if not isinstance(rule, dict):
            raise ValueError("Each rule must be a dictionary.")

        missing = [
            field
            for field in self.REQUIRED_FIELDS
            if field not in rule
        ]

        if missing:
            raise ValueError(
                f"Rule is missing fields: {missing}"
            )

        rule["rule_id"] = self.normalize_rule_id(
            rule["rule_id"]
        )

        # Required text fields
        for field in [
            "category",
            "transformation_type",
            "description"
        ]:

            if not isinstance(rule[field], str) or not rule[field].strip():

                raise ValueError(
                    f"{rule['rule_id']}: {field} is empty."
                )

        # String compatibility fields
        for field in [
            "element_type",
            "source",
            "target",
            "source_module",
            "target_module",
            "source_excerpt"
        ]:

            if not isinstance(rule[field], str):
                raise ValueError(
                    f"{rule['rule_id']}: {field} must be a string."
                )

        # List fields
        for field in [
            "targets",
            "operations",
            "preconditions",
            "required_changes",
            "safety_conditions"
        ]:

            if not isinstance(rule[field], list):
                raise ValueError(
                    f"{rule['rule_id']}: {field} must be a list."
                )

        # Validate targets
        for target in rule["targets"]:

            if not isinstance(target, dict):
                raise ValueError(
                    f"{rule['rule_id']}: invalid target."
                )

            missing_target_fields = [
                field
                for field in self.TARGET_FIELDS
                if field not in target
            ]

            if missing_target_fields:
                raise ValueError(
                    f"{rule['rule_id']}: target missing "
                    f"{missing_target_fields}"
                )

            for field in self.TARGET_FIELDS:

                if not isinstance(target[field], str):
                    raise ValueError(
                        f"{rule['rule_id']}: target field "
                        f"{field} must be a string."
                    )

        # Validate operations
        for operation in rule["operations"]:

            if not isinstance(operation, dict):
                raise ValueError(
                    f"{rule['rule_id']}: operation must be an object."
                )

            operation_type = operation.get("operation")

            if not isinstance(operation_type, str) or not operation_type.strip():
                raise ValueError(
                    f"{rule['rule_id']}: operation type is missing."
                )

        # Validate examples
        if not isinstance(rule["examples"], dict):
            raise ValueError(
                f"{rule['rule_id']}: examples must be an object."
            )

        for field in ["before", "after"]:

            if field not in rule["examples"]:
                raise ValueError(
                    f"{rule['rule_id']}: examples missing {field}."
                )

            if not isinstance(rule["examples"][field], str):
                raise ValueError(
                    f"{rule['rule_id']}: example {field} must be a string."
                )

        # A rule without operations must explicitly request review.
        if not rule["operations"]:

            raise ValueError(
                f"{rule['rule_id']}: no structured operations. "
                "Use a manual_review operation if the rule "
                "cannot be safely expressed."
            )

    # ==================================================
    # 10. VALIDATE A BATCH
    # ==================================================

    def validate_batch(
        self,
        rules: list[dict],
        expected_ids: list[str]
    ):

        if len(rules) != len(expected_ids):

            raise ValueError(
                f"Expected {len(expected_ids)} rules "
                f"{expected_ids}, but received {len(rules)}."
            )

        actual_ids = []

        for rule in rules:

            self.validate_rule(rule)
            actual_ids.append(rule["rule_id"])

        if len(actual_ids) != len(set(actual_ids)):
            raise ValueError(
                "Duplicate rule IDs found in batch."
            )

        if set(actual_ids) != set(expected_ids):

            raise ValueError(
                f"Batch rule IDs do not match. "
                f"Expected {expected_ids}, got {actual_ids}."
            )

    # ==================================================
    # 11. EXTRACT ONE BATCH
    # ==================================================

    def extract_batch(
        self,
        batch_text: str,
        expected_ids: list[str]
    ) -> list[dict]:

        prompt = self.build_prompt(batch_text)

        content = self.call_llm(prompt)

        rules = self.parse_response(content)

        self.validate_batch(rules, expected_ids)

        print(
            "Rules extracted in this batch:",
            len(rules)
        )

        return rules

    # ==================================================
    # 12. DOCUMENT AND PROMPT FINGERPRINT
    # ==================================================

    def get_fingerprint(self, document_text: str) -> str:

        content = (
            self.normalize_text(document_text)
            + self.PROMPT_VERSION
            + str(self.SCHEMA_VERSION)
            + str(self.BATCH_SIZE)
        )

        return hashlib.sha256(
            content.encode("utf-8")
        ).hexdigest()

    # ==================================================
    # 13. SAVE CHECKPOINT
    # ==================================================

    def save_checkpoint(
        self,
        batch_index: int,
        rules: list[dict],
        fingerprint: str
    ):

        self.checkpoint_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        checkpoint = {
            "schema_version": self.SCHEMA_VERSION,
            "prompt_version": self.PROMPT_VERSION,
            "fingerprint": fingerprint,
            "last_completed_batch": batch_index,
            "rules": rules
        }

        temporary_path = self.checkpoint_path.with_suffix(
            ".tmp"
        )

        with open(
            temporary_path,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                checkpoint,
                file,
                indent=4,
                ensure_ascii=False
            )

        temporary_path.replace(self.checkpoint_path)

    # ==================================================
    # 14. LOAD CHECKPOINT
    # ==================================================

    def load_checkpoint(self, fingerprint: str) -> dict:

        empty_checkpoint = {
            "schema_version": self.SCHEMA_VERSION,
            "prompt_version": self.PROMPT_VERSION,
            "fingerprint": fingerprint,
            "last_completed_batch": 0,
            "rules": []
        }

        if not self.checkpoint_path.exists():
            return empty_checkpoint

        try:

            with open(
                self.checkpoint_path,
                "r",
                encoding="utf-8"
            ) as file:

                checkpoint = json.load(file)

        except (json.JSONDecodeError, OSError):

            print(
                "Checkpoint is unreadable. "
                "Starting a fresh extraction."
            )

            return empty_checkpoint

        if (
            checkpoint.get("schema_version") != self.SCHEMA_VERSION
            or checkpoint.get("prompt_version") != self.PROMPT_VERSION
            or checkpoint.get("fingerprint") != fingerprint
        ):

            print(
                "Checkpoint does not match the current "
                "document or extraction version. "
                "Starting fresh."
            )

            return empty_checkpoint

        if (
            not isinstance(checkpoint.get("last_completed_batch"), int)
            or not isinstance(checkpoint.get("rules"), list)
        ):

            print("Invalid checkpoint structure. Starting fresh.")

            return empty_checkpoint

        return checkpoint

    # ==================================================
    # 15. VALIDATE ALL RULES
    # ==================================================

    def validate_all_rules(
        self,
        rules: list[dict],
        batches: list[list[str]]
    ) -> list[dict]:

        expected_ids = {
            f"R{i:02d}"
            for i in range(1, self.EXPECTED_RULE_COUNT + 1)
        }

        actual_ids = []

        for rule in rules:

            self.validate_rule(rule)
            actual_ids.append(rule["rule_id"])

        if len(actual_ids) != len(set(actual_ids)):
            raise ValueError(
                "Duplicate rule IDs found in final extraction."
            )

        actual_set = set(actual_ids)

        missing = expected_ids - actual_set
        unexpected = actual_set - expected_ids

        if missing or unexpected:

            raise ValueError(
                f"Final rule validation failed. "
                f"Missing: {sorted(missing)}, "
                f"Unexpected: {sorted(unexpected)}"
            )

        rules.sort(
            key=lambda item: int(item["rule_id"][1:])
        )

        return rules

    # ==================================================
    # 16. EXTRACT ALL RULES
    # ==================================================

    def extract_rules(self, document_text: str) -> dict:

        if not document_text or not document_text.strip():
            raise ValueError("Migration document is empty.")

        rule_sections = self.split_rules(document_text)

        batches = self.create_batches(rule_sections)

        fingerprint = self.get_fingerprint(document_text)

        checkpoint = self.load_checkpoint(fingerprint)

        last_completed = checkpoint["last_completed_batch"]
        all_rules = checkpoint["rules"]

        if last_completed < 0 or last_completed > len(batches):
            raise ValueError("Invalid checkpoint batch number.")

        # Validate saved rules before resuming.
        if all_rules:

            saved_ids = set()

            for rule in all_rules:
                self.validate_rule(rule)

                if rule["rule_id"] in saved_ids:
                    raise ValueError(
                        "Duplicate rule found in checkpoint."
                    )

                saved_ids.add(rule["rule_id"])

            expected_saved_ids = {
                self.get_rule_id(section)
                for batch in batches[:last_completed]
                for section in batch
            }

            if saved_ids != expected_saved_ids:

                print(
                    "Checkpoint contents are inconsistent. "
                    "Starting extraction again."
                )

                last_completed = 0
                all_rules = []

        print("\n===== BATCH EXTRACTION =====")

        if last_completed:
            print(
                f"Resuming after batch "
                f"{last_completed}/{len(batches)}"
            )

        for index in range(last_completed, len(batches)):

            batch = batches[index]

            expected_ids = [
                self.get_rule_id(section)
                for section in batch
            ]

            print(
                f"\nProcessing batch "
                f"{index + 1}/{len(batches)}"
            )

            batch_text = "\n\n".join(batch)

            extracted_rules = self.extract_batch(
                batch_text,
                expected_ids
            )

            all_rules.extend(extracted_rules)

            # Save after each successfully validated batch.
            self.save_checkpoint(
                index + 1,
                all_rules,
                fingerprint
            )

            print("Checkpoint saved.")

        all_rules = self.validate_all_rules(
            all_rules,
            batches
        )

        print("\n===== EXTRACTION COMPLETED =====")
        print("Total rules:", len(all_rules))
        print("Validated rule IDs:", len(all_rules))

        return {
            "rules": all_rules
        }

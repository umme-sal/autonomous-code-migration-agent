import json
import os
import re

import libcst as cst
from dotenv import load_dotenv
from groq import Groq


load_dotenv()


class MigrationPlanner:

    MODEL = "openai/gpt-oss-120b"

    SUPPORTED_EDIT_TARGETS = {
        "method_name",
        "arguments"
    }

    SUPPORTED_OPERATIONS = {
        "replace"
    }

    def __init__(self):

        api_key = os.getenv("GROQ_API_KEY")

        if not api_key:
            raise ValueError("GROQ_API_KEY is not set.")

        self.client = Groq(api_key=api_key)
        self.model = self.MODEL

    # ==================================================
    # 1. PREPARE MIGRATION RULES
    # ==================================================

    def prepare_rules(
        self,
        migration_rules: list[dict]
    ) -> list[dict]:

        prepared_rules = []

        for rule in migration_rules:

            if not isinstance(rule, dict):
                continue

            prepared_rule = {
                "rule_id": rule.get("rule_id", ""),
                "category": rule.get("category", ""),
                "transformation_type": rule.get(
                    "transformation_type", ""
                ),
                "description": rule.get("description", ""),
                "targets": rule.get("targets", []),
                "operations": rule.get("operations", []),
                "preconditions": rule.get("preconditions", []),
                "required_changes": rule.get(
                    "required_changes", []
                ),
                "safety_conditions": rule.get(
                    "safety_conditions", []
                ),
                "examples": rule.get("examples", {})
            }

            prepared_rules.append(prepared_rule)

        return prepared_rules

    # ==================================================
    # 2. PREPARE RETRIEVED DOCUMENTATION
    # ==================================================

    def prepare_documentation(
        self,
        retrieved_docs: list[dict]
    ) -> str:

        if not retrieved_docs:
            return "No supporting documentation retrieved."

        documentation_parts = []

        for index, item in enumerate(retrieved_docs, start=1):

            if not isinstance(item, dict):
                continue

            text = item.get("text", "")

            if not isinstance(text, str) or not text.strip():
                continue

            documentation_parts.append(
                f"DOCUMENT {index}:\n{text.strip()}"
            )

        if not documentation_parts:
            return "No usable supporting documentation retrieved."

        return "\n\n".join(documentation_parts)

    # ==================================================
    # 3. BUILD PROMPT
    # ==================================================

    def build_prompt(
        self,
        source_code: str,
        retrieved_docs: list[dict],
        migration_rules: list[dict]
    ) -> str:

        documentation = self.prepare_documentation(
            retrieved_docs
        )

        prepared_rules = self.prepare_rules(
            migration_rules
        )

        rules_json = json.dumps(
            prepared_rules,
            indent=4,
            ensure_ascii=False
        )

        return f"""
You are an expert Python code migration planner.

Your task is to analyze Python source code and produce
a structured edit plan using ONLY the supplied migration
rules and supporting documentation.

You do NOT modify source code directly.

You only propose structured edits for the migration engine.

==================================================
STRICT MIGRATION RULES
==================================================

1. Use only explicitly provided migration rules.
2. Never invent a migration.
3. Use supporting documentation as evidence.
4. Do not rewrite the complete source code.
5. Every target_code must represent a complete function
   call expression in the original source. Preserve the
   expression's structure; whitespace and line breaks do
   not need to be identical.
6. Do not modify code that does not match a migration rule.
7. Do not infer missing parameter values.
8. Respect every precondition.
9. Respect every safety condition.
10. If a required transformation is unsupported,
    do not create an executable edit.
11. Do not guess when the source code is ambiguous.
12. If a rule requires manual review, do not apply it.
13. Do not generate duplicate targets.
14. Preserve unrelated arguments and method calls.

==================================================
AVAILABLE EDIT CAPABILITIES
==================================================

The current migration engine supports only:

1. method_name
2. arguments

The supported operation is:

replace

Do not generate other edit targets or operations.

==================================================
EDIT FORMAT
==================================================

For method_name:

{{
    "target": "method_name",
    "operation": "replace",
    "value": {{
        "type": "identifier",
        "name": "invoke"
    }}
}}

For arguments:

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

Argument value nodes may use these types:

- identifier
- string
- integer
- float
- boolean
- none
- call
- dictionary
- list
- tuple
- attribute

Use the appropriate representation for the expression.

Do not use an unsupported node type.

==================================================
HOW TO USE MIGRATION OPERATIONS
==================================================

Each migration rule may contain:

- targets
- operations
- preconditions
- required_changes
- safety_conditions

Use these fields to understand the intended transformation.

The operations field describes what should change.

The targets field identifies affected code elements.

The required_changes field provides additional details.

The safety_conditions field specifies when a transformation
must not be performed.

The examples field provides before-and-after guidance.

However, the current migration engine can execute only
method_name and arguments replacements.

Examples:

A rule with rename_method may be converted into a
method_name replacement if the exact call exists.

A rule with rename_keyword_argument may be converted
into an arguments replacement if the exact call exists.

A rule with positional_to_keyword_argument may be
converted into an arguments replacement if the target
call and argument value are unambiguous.

A rule requiring import migration, class migration,
async propagation, exception handling, configuration
restructuring, or other unsupported transformations
must not be converted into an executable edit.

==================================================
MANUAL REVIEW
==================================================

If a matching rule requires a transformation that the
current engine cannot perform safely, add its rule ID
to manual_review.

Examples:

- rename_exception_class
- modify_exception_handling_structure
- propagate_async
- replace_sync_iteration
- restructure_configuration
- replace_constructor
- change_base_class

Do not pretend these transformations have been applied.

If a safety condition is not satisfied or cannot be verified,
add the rule ID to manual_review.

==================================================
SOURCE CODE
==================================================

{source_code}

==================================================
MIGRATION RULES
==================================================

{rules_json}

==================================================
SUPPORTING DOCUMENTATION
==================================================

{documentation}

==================================================
OUTPUT FORMAT
==================================================

Return ONLY valid JSON.

Use exactly this structure:

{{
    "migration_required": true,
    "targets": [
        {{
            "target_code": "complete function call expression from original source",
            "edits": [
                {{
                    "target": "method_name",
                    "operation": "replace",
                    "value": {{
                        "type": "identifier",
                        "name": "invoke"
                    }}
                }}
            ]
        }}
    ],
    "manual_review": []
}}

If no executable migration is required:

{{
    "migration_required": false,
    "targets": [],
    "manual_review": []
}}

If a migration is required but unsupported by the current
engine, return migration_required=false, targets=[],
and include the relevant rule IDs in manual_review.

Do not include explanations outside the JSON.
"""

    # ==================================================
    # 4. PARSE JSON RESPONSE
    # ==================================================

    def parse_response(self, content: str) -> dict:

        content = content.strip()

        # Remove Markdown code fences.
        content = re.sub(
            r"^```(?:json)?\s*",
            "",
            content,
            flags=re.IGNORECASE
        )

        content = re.sub(
            r"\s*```$",
            "",
            content
        )

        try:
            result = json.loads(content)

        except json.JSONDecodeError as error:
            raise ValueError(
                f"LLM returned invalid JSON: {error}"
            ) from error

        if not isinstance(result, dict):
            raise ValueError(
                "Edit plan must be a JSON object."
            )

        return result

    # ==================================================
    # 5. VALIDATE EDIT NODE VALUES
    # ==================================================

    def validate_value_node(self, value):

        if not isinstance(value, dict):
            raise ValueError("Edit value must be a dictionary.")

        node_type = value.get("type")

        allowed_types = {
            "identifier",
            "string",
            "integer",
            "float",
            "boolean",
            "none",
            "call",
            "dictionary",
            "list",
            "tuple",
            "attribute"
        }

        if node_type not in allowed_types:
            raise ValueError(
                f"Unsupported value node type: {node_type}"
            )

        if node_type == "identifier":

            if not isinstance(value.get("name"), str):
                raise ValueError("Identifier node requires a name.")

            if not value["name"].isidentifier():
                raise ValueError("Identifier name is invalid.")

        elif node_type == "string":

            if not isinstance(value.get("value"), str):
                raise ValueError("String node requires a string value.")

        elif node_type == "integer":

            if not isinstance(value.get("value"), int) or isinstance(value.get("value"), bool):
                raise ValueError("Integer node requires an integer value.")

        elif node_type == "float":

            if not isinstance(value.get("value"), (int, float)) or isinstance(value.get("value"), bool):
                raise ValueError("Float node requires a numeric value.")

        elif node_type == "boolean":

            if not isinstance(value.get("value"), bool):
                raise ValueError("Boolean node requires a boolean value.")

        elif node_type == "none":
            pass

        elif node_type == "attribute":

            self.validate_value_node(value.get("value"))

            if not isinstance(value.get("attr"), str) or not value["attr"].isidentifier():
                raise ValueError("Attribute node requires a valid attribute name.")

        elif node_type == "call":

            self.validate_value_node(value.get("function"))

            arguments = value.get("arguments", [])

            if not isinstance(arguments, list):
                raise ValueError("Call arguments must be a list.")

            for argument in arguments:

                if not isinstance(argument, dict):
                    raise ValueError("Call argument must be a dictionary.")

                argument_type = argument.get("type")

                if argument_type == "positional_argument":
                    self.validate_value_node(argument.get("value"))

                elif argument_type == "keyword_argument":

                    name = argument.get("name")

                    if not isinstance(name, str) or not name.isidentifier():
                        raise ValueError("Invalid keyword argument name.")

                    self.validate_value_node(argument.get("value"))

                else:
                    raise ValueError("Unsupported call argument type.")

        elif node_type in {"list", "tuple"}:

            elements = value.get("elements")

            if not isinstance(elements, list):
                raise ValueError(
                    f"{node_type} node requires an elements list."
                )

            for element in elements:
                self.validate_value_node(element)

        elif node_type == "dictionary":

            entries = value.get("entries")

            if not isinstance(entries, list):
                raise ValueError("Dictionary node requires an entries list.")

            for entry in entries:

                if not isinstance(entry, dict):
                    raise ValueError("Dictionary entry must be a dictionary.")

                if not isinstance(entry.get("key"), str):
                    raise ValueError("Dictionary key must be a string.")

                self.validate_value_node(entry.get("value"))

    # ==================================================
    # 6. VALIDATE ONE EDIT
    # ==================================================

    def validate_edit(self, edit: dict):

        if not isinstance(edit, dict):
            raise ValueError("Each edit must be a dictionary.")

        target = edit.get("target")
        operation = edit.get("operation")

        if target not in self.SUPPORTED_EDIT_TARGETS:
            raise ValueError(
                f"Unsupported edit target: {target}"
            )

        if operation not in self.SUPPORTED_OPERATIONS:
            raise ValueError(
                f"Unsupported edit operation: {operation}"
            )

        value = edit.get("value")

        if target == "method_name":

            if not isinstance(value, dict):
                raise ValueError(
                    "method_name value must be a dictionary."
                )

            if value.get("type") != "identifier":
                raise ValueError(
                    "method_name must use an identifier node."
                )

            if not isinstance(value.get("name"), str):
                raise ValueError(
                    "New method name must be a string."
                )

            if not value["name"].isidentifier():
                raise ValueError(
                    "New method name must be a valid identifier."
                )

        elif target == "arguments":

            if not isinstance(value, list):
                raise ValueError(
                    "arguments value must be a list."
                )

            for argument in value:

                if not isinstance(argument, dict):
                    raise ValueError(
                        "Each argument must be a dictionary."
                    )

                argument_type = argument.get("type")

                if argument_type == "keyword_argument":

                    if not isinstance(argument.get("name"), str):
                        raise ValueError(
                            "Keyword argument requires a name."
                        )

                    if not argument["name"].isidentifier():
                        raise ValueError(
                            "Keyword argument name must be a valid identifier."
                        )

                    self.validate_value_node(
                        argument.get("value")
                    )

                elif argument_type == "positional_argument":

                    self.validate_value_node(
                        argument.get("value")
                    )

                else:
                    raise ValueError(
                        f"Unsupported argument type: {argument_type}"
                    )

    # ==================================================
    # 7. STRUCTURAL TARGET MATCHING
    # ==================================================

    def count_matching_targets(
        self,
        source_code: str,
        target_code: str
    ) -> int:
        """
        Count structurally matching call expressions.

        LibCST deep_equals compares syntax-tree structure while
        ignoring formatting differences such as spaces and
        line breaks. This allows a multiline source call to
        match a compact target expression returned by the LLM.
        """

        try:
            source_tree = cst.parse_module(source_code)
            target_tree = cst.parse_expression(target_code)

        except (cst.ParserSyntaxError, TypeError, ValueError):
            return 0

        if not isinstance(target_tree, cst.Call):
            return 0

        class TargetFinder(cst.CSTVisitor):

            def __init__(self, expected_target):
                self.expected_target = expected_target
                self.count = 0

            def visit_Call(self, node):
                if node.deep_equals(self.expected_target):
                    self.count += 1

        finder = TargetFinder(target_tree)
        source_tree.visit(finder)

        return finder.count

    # ==================================================
    # 8. VALIDATE COMPLETE EDIT PLAN
    # ==================================================

    def validate_edit_plan(
        self,
        edit_plan: dict,
        source_code: str
    ) -> dict:

        if not isinstance(edit_plan, dict):
            raise ValueError("Edit plan must be a dictionary.")

        if not isinstance(edit_plan.get("migration_required"), bool):
            raise ValueError(
                "migration_required must be boolean."
            )

        targets = edit_plan.get("targets")

        if not isinstance(targets, list):
            raise ValueError(
                "targets must be a list."
            )

        manual_review = edit_plan.get("manual_review", [])

        if not isinstance(manual_review, list):
            raise ValueError(
                "manual_review must be a list."
            )

        if not all(isinstance(item, str) for item in manual_review):
            raise ValueError(
                "manual_review entries must be strings."
            )

        seen_targets = set()

        for target in targets:

            if not isinstance(target, dict):
                raise ValueError(
                    "Each target must be a dictionary."
                )

            target_code = target.get("target_code")

            if not isinstance(target_code, str) or not target_code.strip():
                raise ValueError(
                    "target_code must be a non-empty string."
                )

            # Match the LLM target against the original source
            # structurally, not by exact whitespace-sensitive text.
            occurrences = self.count_matching_targets(
                source_code,
                target_code
            )

            if occurrences == 0:
                raise ValueError(
                    "Target code does not structurally match "
                    f"any call in source: {target_code}"
                )

            if occurrences > 1:
                raise ValueError(
                    f"Ambiguous target: '{target_code}' appears "
                    f"{occurrences} times in source."
                )

            if target_code in seen_targets:
                raise ValueError(
                    f"Duplicate target detected: {target_code}"
                )

            seen_targets.add(target_code)

            edits = target.get("edits")

            if not isinstance(edits, list) or not edits:
                raise ValueError(
                    "Every target must contain at least one edit."
                )

            seen_edit_targets = set()

            for edit in edits:

                self.validate_edit(edit)

                edit_target = edit["target"]

                if edit_target in seen_edit_targets:
                    raise ValueError(
                        f"Duplicate edit target: {edit_target}"
                    )

                seen_edit_targets.add(edit_target)

        if edit_plan["migration_required"] and not targets:
            raise ValueError(
                "migration_required is true but targets is empty."
            )

        if not targets:
            edit_plan["migration_required"] = False

        return edit_plan

    # ==================================================
    # 9. GENERATE EDIT PLAN
    # ==================================================

    def generate_edit_plan(
        self,
        source_code: str,
        retrieved_docs: list[dict],
        migration_rules: list[dict]
    ) -> dict:

        empty_plan = {
            "migration_required": False,
            "targets": [],
            "manual_review": []
        }

        if not source_code or not source_code.strip():
            return empty_plan

        if not migration_rules:
            return empty_plan

        # Documentation is supporting evidence. Rules remain
        # the source of permitted migration transformations.
        if retrieved_docs is None:
            retrieved_docs = []

        prompt = self.build_prompt(
            source_code,
            retrieved_docs,
            migration_rules
        )

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

        if choice.finish_reason == "length":
            raise ValueError(
                "The edit plan response was truncated. "
                "Reduce the amount of source code or rules."
            )

        content = choice.message.content

        if not content:
            raise ValueError(
                "The LLM returned an empty response."
            )

        edit_plan = self.parse_response(content)

        edit_plan = self.validate_edit_plan(
            edit_plan,
            source_code
        )

        return edit_plan


# ================================================================
# Deterministic async migration planning (R18 / R19)
# ================================================================

def _async_rule_plan(self, source_code: str, retrieved_docs: list[dict], migration_rules: list[dict]) -> dict:
    """Build a conservative async plan from the explicit R18/R19 metadata.

    The LLM remains responsible for ordinary supported call edits. Async
    propagation is derived from Python's AST so the caller graph is explicit
    and reviewable.
    """
    import ast as _ast

    async_rules = [
        rule for rule in migration_rules
        if isinstance(rule, dict)
        and rule.get("transformation_type") in {"convert_to_async", "propagate_async"}
    ]
    standard_rules = [
        rule for rule in migration_rules
        if rule not in async_rules
    ]

    # Preserve the existing planner behavior for all non-async rules.
    if standard_rules:
        plan = self._generate_standard_edit_plan(source_code, retrieved_docs or [], standard_rules)
    else:
        plan = {"migration_required": False, "targets": [], "manual_review": []}

    plan.setdefault("manual_review", [])
    plan.setdefault("targets", [])
    plan.setdefault("migration_required", False)
    plan["async_operations"] = {"functions": [], "await_calls": []}

    if not async_rules or not source_code.strip():
        return plan

    try:
        tree = _ast.parse(source_code)
    except SyntaxError:
        plan["manual_review"].extend(r.get("rule_id", "ASYNC") for r in async_rules)
        return plan

    function_nodes = {}
    parent_function = {}

    class ScopeVisitor(_ast.NodeVisitor):
        def __init__(self):
            self.stack = []

        def visit_FunctionDef(self, node):
            function_nodes.setdefault(node.name, []).append(node)
            self.stack.append(node.name)
            for child in node.body:
                self.visit(child)
            self.stack.pop()

        def visit_AsyncFunctionDef(self, node):
            function_nodes.setdefault(node.name, []).append(node)
            self.stack.append(node.name)
            for child in node.body:
                self.visit(child)
            self.stack.pop()

        def visit_Call(self, node):
            if self.stack:
                parent_function[id(node)] = self.stack[-1]
            self.generic_visit(node)

    ScopeVisitor().visit(tree)

    # R18 gives the seed function and the exact client call to await.
    seed_functions = set()
    seed_api_calls = []
    for rule in async_rules:
        if rule.get("transformation_type") != "convert_to_async":
            continue
        for operation in rule.get("operations", []):
            if not isinstance(operation, dict):
                continue
            if operation.get("operation") == "convert_to_async" and operation.get("function"):
                seed_functions.add(operation["function"])
            elif operation.get("operation") == "add_await" and operation.get("call"):
                seed_api_calls.append(operation["call"])

    # Match R18 only when the named function and exact call expression exist.
    def ast_key(node):
        return _ast.dump(node, include_attributes=False)

    api_call_keys = set()
    for call_text in seed_api_calls:
        try:
            parsed = _ast.parse(call_text, mode="eval").body
            if isinstance(parsed, _ast.Call):
                api_call_keys.add(ast_key(parsed))
        except SyntaxError:
            continue

    matched_seeds = set()
    for seed in seed_functions:
        for fn in function_nodes.get(seed, []):
            if isinstance(fn, _ast.AsyncFunctionDef):
                continue
            found = any(
                isinstance(node, _ast.Call) and ast_key(node) in api_call_keys
                for node in _ast.walk(fn)
            )
            if found:
                matched_seeds.add(seed)

    if not matched_seeds:
        plan["manual_review"].extend(r.get("rule_id", "ASYNC") for r in async_rules)
        return plan

    # Build caller -> callee edges for functions defined in this module.
    callers_by_callee = {}
    module_level_calls = []
    for fn_name, definitions in function_nodes.items():
        for fn in definitions:
            for node in _ast.walk(fn):
                if isinstance(node, _ast.Call) and isinstance(node.func, _ast.Name):
                    called = node.func.id
                    if called in function_nodes:
                        callers_by_callee.setdefault(called, set()).add(fn_name)

    # Recursively propagate from the R18 seed to every in-file caller.
    affected = set(matched_seeds)
    queue = list(matched_seeds)
    while queue:
        callee = queue.pop(0)
        for caller in callers_by_callee.get(callee, set()):
            if caller not in affected:
                affected.add(caller)
                queue.append(caller)

    # A synchronous entry point is a hard boundary under R19's safety rules.
    # Do not partially convert a chain that would leave a synchronous caller
    # invoking a coroutine without awaiting it.
    boundary_names = {"main"}
    boundaries = sorted(name for name in affected if name in boundary_names)
    if boundaries:
        plan["manual_review"].extend(r.get("rule_id", "ASYNC") for r in async_rules)
        plan["async_manual_review"] = [
            f"Synchronous entry point(s) {', '.join(boundaries)} call the async chain; "
            "automatic migration was withheld. Do not add asyncio.run() automatically."
        ]
        return plan

    # If any affected function has multiple definitions, the call graph is
    # ambiguous; withhold the automatic transformation.
    if any(len(function_nodes.get(name, [])) != 1 for name in affected):
        plan["manual_review"].extend(r.get("rule_id", "ASYNC") for r in async_rules)
        plan["async_manual_review"] = ["Ambiguous function definitions in async caller chain."]
        return plan

    # Convert the API call in the seed, and await each affected function call
    # from its caller. ast.unparse produces formatting-independent target text.
    await_targets = set()
    for fn_name in affected:
        fn = function_nodes[fn_name][0]
        for node in _ast.walk(fn):
            if not isinstance(node, _ast.Call):
                continue
            if fn_name in matched_seeds and ast_key(node) in api_call_keys:
                await_targets.add(_ast.unparse(node))
            elif isinstance(node.func, _ast.Name) and node.func.id in affected and node.func.id != fn_name:
                await_targets.add(_ast.unparse(node))

    plan["async_operations"] = {
        "functions": sorted(affected),
        "await_calls": sorted(await_targets),
        "rule_ids": sorted(r.get("rule_id", "") for r in async_rules),
    }
    return plan


# Keep the original LLM-based implementation for ordinary supported edits.
MigrationPlanner._generate_standard_edit_plan = MigrationPlanner.generate_edit_plan
MigrationPlanner.generate_edit_plan = _async_rule_plan

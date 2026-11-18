
from agent2.code_rewriter import CodeRewriter

rewriter = CodeRewriter()

old_code = """
def create_model():
    model = ChatOpenAI()
    return model
"""

migration_rules = """
Replace the deprecated ChatOpenAI import and usage
with the supported modern API according to the migration context.
"""

documentation = """
ChatOpenAI should be imported from langchain_openai
in the updated LangChain version.
"""

new_code = rewriter.rewrite(
    code=old_code,
    migration_rules=migration_rules,
    documentation=documentation
)

print("===== REWRITTEN CODE =====")
print(new_code)

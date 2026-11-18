from agent2.code_parser import CodeParser
from agent2.code_analyzer import CodeAnalyzer

source_code = """
from langchain.chat_models import ChatOpenAI

def create_model():
    model = ChatOpenAI()
    return model

def calculate_total(items):
    return sum(items)
"""

# Use the migration rules already stored in your project
from agent1.rule_store import RuleStore

rule_store = RuleStore()
rule_store.load("vector_store/migration_rules.json")

migration_rules = rule_store.get_rules()

parser = CodeParser()
tree = parser.parse(source_code)

analyzer = CodeAnalyzer(migration_rules)
tree.visit(analyzer)

print("\nDetected functions:")
print(analyzer.functions)

print("\nAffected functions:")
for function in analyzer.affected_functions:
    print("\nFunction:", function["name"])
    print(function["code"])
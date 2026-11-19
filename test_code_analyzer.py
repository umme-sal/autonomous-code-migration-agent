from agent1.agent import MigrationKnowledgeAgent
from agent2.code_analyzer import CodeAnalyzer
import libcst as cst

agent1 = MigrationKnowledgeAgent()
rules = agent1.get_rules()

source_code = """
from langchain.chat_models import ChatOpenAI

class ModelService:

    def create_model(self):

        def initialize():
            llm = ChatOpenAI()
            return llm

        return initialize()
"""

analyzer = CodeAnalyzer(rules)

module = cst.parse_module(source_code)
module.visit(analyzer)

print("\\n===== MIGRATION CANDIDATES =====")

for candidate in analyzer.migration_candidates:
    print(candidate)

print("\\n===== AFFECTED FUNCTIONS =====")

for function in analyzer.affected_functions:
    print(function["name"])
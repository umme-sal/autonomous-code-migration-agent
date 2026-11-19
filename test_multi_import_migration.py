
from agent1.agent import MigrationKnowledgeAgent
from agent2.migration_engine import MigrationEngine

agent1 = MigrationKnowledgeAgent()
rules = agent1.get_rules()

source_code = """
from langchain.vectorstores import FAISS, Chroma

db1 = FAISS.from_texts(["hello"], embeddings)
db2 = Chroma.from_texts(["hello"], embeddings)
"""

engine = MigrationEngine()
migrated_code = engine.migrate(source_code, rules)

print("\n===== ORIGINAL CODE =====")
print(source_code)

print("\n===== MIGRATED CODE =====")
print(migrated_code)

expected_imports = [
    "from langchain_community.vectorstores import FAISS",
    "from langchain_chroma import Chroma",
]

for expected in expected_imports:
    print(
        f"{expected}:",
        "PASS" if expected in migrated_code else "FAIL"
    )

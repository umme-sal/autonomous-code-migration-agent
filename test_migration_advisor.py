from agent2.migration_advisor import MigrationAdvisor


def main():

    source_code = """
from langchain.chat_models import ChatOpenAI

llm = ChatOpenAI()
"""

    candidate = {
        "type": "import",
        "code": "from langchain.chat_models import ChatOpenAI",
        "module": "langchain.chat_models",
        "symbol": "ChatOpenAI",
        "rule": {
            "type": "symbol",
            "source": "ChatOpenAI",
            "target": "ChatOpenAI",
            "source_module": "langchain.chat_models",
            "target_module": "langchain_openai"
        }
    }

    documentation = [
        {
            "score": 0.7849,
            "source": "langchain_langgraph_migration_guide.pdf",
            "text": """
Rule 2 — ChatOpenAI import

Legacy:
from langchain.chat_models import ChatOpenAI

Modern:
from langchain_openai import ChatOpenAI

Migration note:
Apply this rule only when the source construct matches
the documented legacy form.
"""
        }
    ]

    advisor = MigrationAdvisor()

    result = advisor.create_migration_map(
        source_code=source_code,
        candidate=candidate,
        documentation=documentation
    )

    print("\n" + "=" * 70)
    print("MIGRATION ADVISOR RESULT")
    print("=" * 70)

    print(result)


if __name__ == "__main__":
    main()
from agent2.agent import CodeMigrationAgent


def main():

    source_code = """
from langchain.chat_models import ChatOpenAI
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter

llm = ChatOpenAI()
embeddings = OpenAIEmbeddings()

vectorstore = FAISS.from_documents(
    [],
    embeddings
)

splitter = RecursiveCharacterTextSplitter(
    chunk_size=500
)
"""

    agent = CodeMigrationAgent()

    knowledge = agent.retrieve_knowledge(source_code)

    print("\n" + "=" * 70)
    print("FINAL KNOWLEDGE RESULTS")
    print("=" * 70)

    for item in knowledge:

        print("\nCandidate:")
        print(item["candidate"]["code"])

        print("\nNumber of documents retrieved:")
        print(len(item["results"]))


if __name__ == "__main__":
    main()
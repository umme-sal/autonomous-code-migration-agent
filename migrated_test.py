# ============================================================
# Legacy LangChain application
# This comment should remain unchanged after migration.
# ============================================================

from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter


# Initialize the language model
llm = ChatOpenAI()

# Create embeddings for documents
embeddings = OpenAIEmbeddings()


def build_vector_store(documents):
    """
    Build a vector store from the given documents.
    
    This function uses the legacy FAISS integration.
    """

    # Split documents into smaller chunks
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )

    chunks = splitter.split_documents(documents)

    # Create the FAISS vector store
    vectorstore = FAISS.from_documents(
        chunks,
        embeddings
    )

    return vectorstore


def ask_question(question):
    # Send a question to the language model
    response = llm.invoke(question)

    return response


# Example usage
documents = []

# Build the vector store
store = build_vector_store(documents)

# Ask a question
answer = ask_question("What is Python?")

print(answer)

# IMPORTANT:
# The word "ChatOpenAI" inside this comment should NOT be changed.
# The string "from langchain.chat_models import ChatOpenAI"
# should also remain unchanged.

message = "ChatOpenAI is a language model"
print(message)
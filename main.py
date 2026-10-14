from agent1.document_loader import load_document
from agent1.chunker import chunk_text
from agent1.embeddings import EmbeddingModel
from agent1.vector_store import VectorStore
from agent1.retriever import Retriever


file_path = "documents/migration_docs/langChain_readable.pdf"


# -----------------------------------------
# Load document
# -----------------------------------------

text = load_document(file_path)

chunks = chunk_text(text)

print(f"Document words: {len(text.split())}")
print(f"Total chunks: {len(chunks)}")


# -----------------------------------------
# Embeddings
# -----------------------------------------

embedding_model = EmbeddingModel()

embeddings = embedding_model.embed_documents(chunks)

print(f"Embedding shape: {embeddings.shape}")


# -----------------------------------------
# FAISS
# -----------------------------------------

dimension = embeddings.shape[1]

vector_store = VectorStore(dimension)

vector_store.add(embeddings)

print(f"Vectors stored: {vector_store.size()}")


# -----------------------------------------
# Retriever
# -----------------------------------------

retriever = Retriever(
    vector_store=vector_store,
    embedding_model=embedding_model,
    top_k=4,
    similarity_threshold=0.65
)


# -----------------------------------------
# Query
# -----------------------------------------

query = "How does middleware control agent execution?"

results = retriever.retrieve(query)


# -----------------------------------------
# Results
# -----------------------------------------

print("\n" + "=" * 60)
print("RETRIEVED MIGRATION KNOWLEDGE")
print("=" * 60)

if not results:

    print("\nNo relevant migration information found.")

else:

    for rank, result in enumerate(results, start=1):

        index = result["chunk_index"]
        score = result["score"]

        print(f"\nRank {rank}")
        print(f"Score: {score:.4f}")
        print(f"Chunk index: {index}")

        print("\nChunk:")
        print(chunks[index])
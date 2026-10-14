from agent1.embeddings import EmbeddingModel
from agent1.vector_store import VectorStore


class Retriever:

    def __init__(
        self,
        vector_store: VectorStore,
        embedding_model: EmbeddingModel,
        top_k: int = 4,
        similarity_threshold: float = 0.65
    ):
        self.vector_store = vector_store
        self.embedding_model = embedding_model
        self.top_k = top_k
        self.similarity_threshold = similarity_threshold

    def retrieve(self, query: str) -> list[dict]:

        query_embedding = self.embedding_model.embed_query(query)

        scores, indices = self.vector_store.search(
            query_embedding,
            top_k=self.top_k
        )

        results = []

        for score, index in zip(scores, indices):

            # Ignore FAISS invalid indices
            if index == -1:
                continue

            # Apply similarity threshold
            if score < self.similarity_threshold:
                continue

            results.append({
                "score": float(score),
                "chunk_index": int(index)
            })

        return results
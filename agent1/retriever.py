from agent1.embeddings import EmbeddingModel
from agent1.metadata_store import MetadataStore
from agent1.vector_store import VectorStore


class Retriever:

    def __init__(
        self,
        vector_store: VectorStore,
        metadata_store: MetadataStore,
        embedding_model: EmbeddingModel,
        top_k: int = 4,
        similarity_threshold: float = 0.65
    ):

        self.vector_store = vector_store
        self.metadata_store = metadata_store
        self.embedding_model = embedding_model

        self.top_k = top_k
        self.similarity_threshold = similarity_threshold

    def retrieve(self, query: str) -> list[dict]:

        query_embedding = (
            self.embedding_model.embed_query(query)
        )

        scores, indices = self.vector_store.search(
            query_embedding,
            self.top_k
        )

        results = []

        for score, index in zip(scores, indices):

            if index == -1:
                continue

            if score < self.similarity_threshold:
                continue

            chunk = self.metadata_store.get(
                int(index)
            )

            if chunk is None:
                continue

            results.append({
                "score": float(score),
                "chunk_id": chunk.chunk_id,
                "text": chunk.text,
                "source": chunk.source
            })

        return results
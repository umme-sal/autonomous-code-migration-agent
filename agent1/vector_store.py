import faiss
import numpy as np


class VectorStore:

    def __init__(self, dimension: int):
        self.dimension = dimension

        # Inner Product works as cosine similarity
        # because our embeddings are normalized.
        self.index = faiss.IndexFlatIP(dimension)

    def add(self, embeddings: np.ndarray):
        embeddings = np.asarray(
            embeddings,
            dtype="float32"
        )

        self.index.add(embeddings)

    def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 4
    ):
        query_embedding = np.asarray(
            query_embedding,
            dtype="float32"
        ).reshape(1, -1)

        scores, indices = self.index.search(
            query_embedding,
            top_k
        )

        return scores[0], indices[0]

    def size(self) -> int:
        return self.index.ntotal
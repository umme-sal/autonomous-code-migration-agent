from pathlib import Path

import faiss
import numpy as np


class VectorStore:

    def __init__(self, dimension: int):
        self.dimension = dimension

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

    def save(self, file_path: str):

        path = Path(file_path)

        path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        faiss.write_index(
            self.index,
            str(path)
        )

    def load(self, file_path: str):

        self.index = faiss.read_index(
            str(file_path)
        )
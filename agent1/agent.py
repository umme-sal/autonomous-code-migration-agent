from pathlib import Path

from agent1.embeddings import EmbeddingModel
from agent1.metadata_store import MetadataStore
from agent1.retriever import Retriever
from agent1.vector_store import VectorStore


class MigrationKnowledgeAgent:

    def __init__(
        self,
        vector_index: str = "vector_store/index.faiss",
        metadata_file: str = "vector_store/metadata.json",
        top_k: int = 4,
        similarity_threshold: float = 0.65
    ):

        self.vector_index = vector_index
        self.metadata_file = metadata_file

        # -----------------------------
        # Check saved data
        # -----------------------------

        if not Path(vector_index).exists():
            raise FileNotFoundError(
                f"Vector index not found: {vector_index}"
            )

        if not Path(metadata_file).exists():
            raise FileNotFoundError(
                f"Metadata file not found: {metadata_file}"
            )

        # -----------------------------
        # Embedding model
        # -----------------------------

        self.embedding_model = EmbeddingModel()

        # -----------------------------
        # Vector store
        # -----------------------------

        self.vector_store = VectorStore(
            dimension=384
        )

        self.vector_store.load(
            vector_index
        )

        # -----------------------------
        # Metadata
        # -----------------------------

        self.metadata_store = MetadataStore()

        self.metadata_store.load(
            metadata_file
        )

        # -----------------------------
        # Retriever
        # -----------------------------

        self.retriever = Retriever(
            vector_store=self.vector_store,
            metadata_store=self.metadata_store,
            embedding_model=self.embedding_model,
            top_k=top_k,
            similarity_threshold=similarity_threshold
        )

    def search(self, query: str) -> list[dict]:

        return self.retriever.retrieve(query)
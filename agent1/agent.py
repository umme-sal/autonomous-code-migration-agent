from pathlib import Path

from agent1.embeddings import EmbeddingModel
from agent1.metadata_store import MetadataStore
from agent1.retriever import Retriever
from agent1.vector_store import VectorStore
from agent1.document_loader import load_document
from agent1.chunker import chunk_text

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
        
    def ingest_document(self, document_path: str):

        # -----------------------------
        # Load document
        # -----------------------------

        text = load_document(document_path)

        source = Path(document_path).name

        # -----------------------------
        # Get next available ID
        # -----------------------------

        start_id = self.metadata_store.next_chunk_id()

        # -----------------------------
        # Create chunks
        # -----------------------------

        chunks = chunk_text(
            text=text,
            source=source,
            start_id=start_id
        )

        # -----------------------------
        # Generate embeddings
        # -----------------------------

        embeddings = self.embedding_model.embed_documents(
            chunks
        )

        # -----------------------------
        # Add to vector store
        # -----------------------------

        self.vector_store.add(
            embeddings
        )

        # -----------------------------
        # Add metadata
        # -----------------------------

        self.metadata_store.add_chunks(
            chunks
        )

        # -----------------------------
        # Save
        # -----------------------------

        self.vector_store.save(
            self.vector_index
        )

        self.metadata_store.save(
            self.metadata_file
        )

        return len(chunks)
        
    def ingest_directory(self, directory_path: str):

        directory = Path(directory_path)

        if not directory.exists():
            raise FileNotFoundError(
                f"Directory not found: {directory_path}"
            )

        supported_extensions = {
            ".pdf",
            ".docx",
            ".txt"
        }

        files = [
            file
            for file in directory.iterdir()
            if file.is_file()
            and file.suffix.lower() in supported_extensions
        ]

        total_chunks = 0

        for file in files:

            print(f"\nIngesting: {file.name}")

            count = self.ingest_document(
                str(file)
            )

            total_chunks += count

            print(f"Added {count} chunks.")

        return total_chunks
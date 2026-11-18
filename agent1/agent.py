
from pathlib import Path

from agent1.embeddings import EmbeddingModel
from agent1.metadata_store import MetadataStore
from agent1.retriever import Retriever
from agent1.vector_store import VectorStore
from agent1.document_loader import load_document
from agent1.chunker import chunk_text
from agent1.rule_extractor import MigrationRuleExtractor
from agent1.rule_store import RuleStore


class MigrationKnowledgeAgent:

    def __init__(
        self,
        vector_index: str = "vector_store/index.faiss",
        metadata_file: str = "vector_store/metadata.json",
        rules_file: str = "vector_store/rules.json",
        top_k: int = 4,
        similarity_threshold: float = 0.50
    ):

        self.vector_index = vector_index
        self.metadata_file = metadata_file
        self.rules_file = rules_file

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

        if Path(vector_index).exists():

            self.vector_store.load(vector_index)

        # -----------------------------
        # Metadata store
        # -----------------------------

        self.metadata_store = MetadataStore()

        if Path(metadata_file).exists():

            self.metadata_store.load(metadata_file)

        # -----------------------------
        # Rule extractor
        # -----------------------------

        self.rule_extractor = MigrationRuleExtractor()

        # -----------------------------
        # Rule store
        # -----------------------------

        self.rule_store = RuleStore()

        if Path(rules_file).exists():

            self.rule_store.load(rules_file)

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

    # ==================================================
    # DOCUMENT RETRIEVAL
    # ==================================================

    def search(self, query: str) -> list[dict]:

        if self.vector_store.size() == 0:
            return []

        return self.retriever.retrieve(query)

    # ==================================================
    # GET MIGRATION RULES
    # ==================================================

    def get_rules(self) -> list[dict]:

        return self.rule_store.get_rules()

    # ==================================================
    # DOCUMENT INGESTION
    # ==================================================

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
        # Add vectors
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
        # Extract migration rules
        # -----------------------------

        extracted_data = self.rule_extractor.extract_rules(
            text
        )

        extracted_rules = extracted_data.get(
            "rules", []
        )

        # -----------------------------
        # Store migration rules
        # -----------------------------

        self.rule_store.add_rules(
            extracted_rules
        )

        # -----------------------------
        # Save all data
        # -----------------------------

        self.vector_store.save(
            self.vector_index
        )

        self.metadata_store.save(
            self.metadata_file
        )

        self.rule_store.save(
            self.rules_file
        )

        return {
            "chunks_added": len(chunks),
            "rules_added": len(extracted_rules)
        }

    # ==================================================
    # DIRECTORY INGESTION
    # ==================================================

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
        total_rules = 0

        for file in files:

            print(f"\nIngesting: {file.name}")

            result = self.ingest_document(
                str(file)
            )

            total_chunks += result["chunks_added"]
            total_rules += result["rules_added"]

            print(
                f"Added {result['chunks_added']} chunks."
            )

            print(
                f"Extracted {result['rules_added']} rules."
            )

        return {
            "total_chunks": total_chunks,
            "total_rules": total_rules
        }

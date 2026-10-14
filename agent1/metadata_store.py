import json
from pathlib import Path

from agent1.models import DocumentChunk


class MetadataStore:

    def __init__(self):
        self.chunks: dict[int, DocumentChunk] = {}

    def add_chunks(
        self,
        chunks: list[DocumentChunk]
    ):
        for chunk in chunks:
            self.chunks[chunk.chunk_id] = chunk

    def get(
        self,
        chunk_id: int
    ) -> DocumentChunk | None:

        return self.chunks.get(chunk_id)

    def save(self, file_path: str):

        path = Path(file_path)

        path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        data = [
            {
                "chunk_id": chunk.chunk_id,
                "text": chunk.text,
                "source": chunk.source
            }
            for chunk in self.chunks.values()
        ]

        with open(
            path,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                data,
                file,
                indent=2,
                ensure_ascii=False
            )

    def load(self, file_path: str):

        with open(
            file_path,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

        self.chunks = {
            item["chunk_id"]: DocumentChunk(
                chunk_id=item["chunk_id"],
                text=item["text"],
                source=item["source"]
            )
            for item in data
        }

    def next_chunk_id(self) -> int:

        if not self.chunks:
            return 0

        return max(self.chunks.keys()) + 1
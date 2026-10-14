from langchain_text_splitters import RecursiveCharacterTextSplitter

from agent1.models import DocumentChunk


def chunk_text(
    text: str,
    source: str,
    chunk_size: int = 100,
    chunk_overlap: int = 20
) -> list[DocumentChunk]:

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=lambda text: len(text.split()),
        separators=[
            "\n\n",
            "\n",
            ". ",
            " ",
            ""
        ]
    )

    chunks = splitter.split_text(text)

    return [
        DocumentChunk(
            chunk_id=i,
            text=chunk,
            source=source
        )
        for i, chunk in enumerate(chunks)
    ]
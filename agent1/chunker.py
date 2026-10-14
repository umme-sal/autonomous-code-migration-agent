from langchain_text_splitters import RecursiveCharacterTextSplitter


def chunk_text(
    text: str,
    chunk_size: int = 100,
    chunk_overlap: int = 20
) -> list[str]:

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

    return splitter.split_text(text)
from pathlib import Path
from pypdf import PdfReader
from docx import Document


def load_pdf(file_path: str) -> str:
    reader = PdfReader(file_path)

    text = []

    for page in reader.pages:
        page_text = page.extract_text()

        if page_text:
            text.append(page_text)

    return "\n".join(text)


def load_docx(file_path: str) -> str:
    document = Document(file_path)

    paragraphs = []

    for paragraph in document.paragraphs:
        if paragraph.text.strip():
            paragraphs.append(paragraph.text)

    return "\n".join(paragraphs)


def load_document(file_path: str) -> str:
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    if path.suffix.lower() == ".pdf":
        return load_pdf(file_path)

    elif path.suffix.lower() == ".docx":
        return load_docx(file_path)

    elif path.suffix.lower() == ".txt":
        return path.read_text(encoding="utf-8")

    else:
        raise ValueError(
            f"Unsupported document type: {path.suffix}"
        )
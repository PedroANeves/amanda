from docx import Document  # type: ignore


def extract_rows(filename: str | type[Document]) -> list[tuple[str, str]]:
    return [("", "")]

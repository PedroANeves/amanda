from docx import Document  # type: ignore


def extract_rows(filename: str | type[Document]) -> list[tuple[str, str]]:
    document = Document(filename)
    table = document.tables[0]
    lines = [tuple(cell.text for cell in row.cells) for row in table.rows]
    return lines

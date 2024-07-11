from docx import Document  # type: ignore


def extract_rows(filename: str | type[Document]) -> list[tuple[str, str]]:
    """Usage: lines = extract_rows('document.docx')

    # document.docx
    .--------------------------------------+----------------------------------.
    |Remember when the cool thing happened?|V1 00:01:15 – Cool thing happened.|
    `--------------------------------------+----------------------------------`

    lines ==[
        (
            "Remember when the cool thing happened?",
            "V1 00:01:15 – Cool thing happened.",
        ),
    ]
    """
    document = Document(filename)
    table = document.tables[0]
    lines = [tuple(cell.text for cell in row.cells) for row in table.rows]
    return lines


EN_DASH = "\u2013"


def extract_timestamps(
    lines: list[tuple[str, str]],
) -> list[tuple[str, str]]:

    return [
        _extract_name_and_timestamp(line)
        for _, line in lines
        if _has_timestamp(line)
    ]


def _extract_name_and_timestamp(from_line: str) -> tuple[str, str]:
    vn_and_timestamp, _comment = from_line.split(f" {EN_DASH} ", maxsplit=1)
    video_number, timestamp = vn_and_timestamp.split(" ", maxsplit=1)
    return video_number, timestamp


def _has_timestamp(line: str) -> bool:
    return line.count(":") == 2 and line.count(EN_DASH) == 1
def main():
    return 0


if __name__ == "__main__":
    exit(main())

import os
import re
from datetime import timedelta

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


PREFIX = r"^(?P<prefix>V\d+).*"
pattern = re.compile(PREFIX)


def _file_has_prefix(file: os.DirEntry) -> bool:
    return file.is_file() and pattern.match(file.name) is not None


def _get_prefix(file: os.DirEntry) -> str:
    m = pattern.match(file.name)
    if m is None:
        raise ValueError()
    return m.groupdict()["prefix"]


# get paths for all Vn
def find_file(this_dir: str | None = None) -> dict[str, str]:
    if not this_dir:
        this_dir = os.path.dirname(os.path.realpath(__file__))

    lines = {
        _get_prefix(file): file.path
        for file in os.scandir(this_dir)
        if _file_has_prefix(file)
    }
    return lines


def _add_time_delta(start: str, delta: int) -> str:
    hs, mins, s = map(int, start.split(":", maxsplit=2))
    start_stamp = timedelta(hours=hs, minutes=mins, seconds=s)
    end = start_stamp + timedelta(seconds=10)

    hours, _remains = divmod(int(end.total_seconds()), 60 * 60)
    minutes, seconds = divmod(_remains, 60)
    return f"{hours:02}:{minutes:02}:{seconds:02}"


def build_lines(timestamps, videos):
    return [
        (videos[prefix], time_start, _add_time_delta(time_start, 10))
        for prefix, time_start in timestamps
    ]


def save_csv(data: list, path: Path) -> None:
    filename = path / "amanda.csv"
    with open(filename, "w") as f:
        f.write("filepath,start,end\n")
        for line in data:
            f.write(f"{line[0]},{line[1]},{line[2]}\n")


def main():
    return 0


if __name__ == "__main__":
    exit(main())

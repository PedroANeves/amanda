# false positive workaround for W0621:redefined-outer-name :
# https://github.com/pylint-dev/pylint/issues/6531
# pylint: disable=redefined-outer-name
import pytest
from docx import Document  # type: ignore

from src.amanda import (
    EN_DASH,
    _add_time_delta,
    _extract_name_and_timestamp,
    _has_timestamp,
    build_lines,
    extract_rows,
    extract_timestamps,
    find_file,
    save_csv,
)

EXAMPLE_LINES = [
    (
        "Remember when the cool thing happened?",
        "V1 00:01:15 – Cool thing happened.",
    ),
    ("This line should be ignored,", "Because there is no timestamp here"),
    (
        "And then other thing happened.",
        "V2 00:05:00 – Other thing.",
    ),
]


@pytest.fixture
def doc(tmp_path):
    filename = tmp_path / "times.docx"
    document = Document()

    table = document.add_table(rows=0, cols=2)
    lines = EXAMPLE_LINES
    for comment, times in lines:
        cells = table.add_row().cells
        cells[0].text = comment
        cells[1].text = times

    document.save(filename)
    return filename


def test_extract_rows(doc):
    assert extract_rows(doc) == EXAMPLE_LINES


def test_extract_timestamps():
    lines = EXAMPLE_LINES

    assert extract_timestamps(lines) == [
        ("V1", "00:01:15"),
        ("V2", "00:05:00"),
    ]


def test__extract_name_and_timestamp():
    assert _extract_name_and_timestamp(
        "V1 00:01:15 – Cool thing happened."
    ) == ("V1", "00:01:15")


def test__has_timestamp():
    assert _has_timestamp("V1 00:01:15 – Cool thing happened.")


@pytest.mark.parametrize(
    "line",
    [
        "This line should be ignored,",
        f"FONTES CONSULTADAS: IMAGENS: {EN_DASH}",
    ],
)
def test_not_has_timestamp(line):
    assert not _has_timestamp(line)


def test_find_file(tmp_path):
    v1_file = tmp_path / "V1 file.txt"
    v1_file.touch()
    n_file = tmp_path / "not a propper file.txt"
    n_file.touch()
    v2_file = tmp_path / "V2 file.txt"
    v2_file.touch()

    assert find_file(tmp_path) == {"V1": str(v1_file), "V2": str(v2_file)}


def test__add_time_delta():
    assert _add_time_delta("00:01:15", 10) == "00:01:25"


def test_build_lines():
    timestamps = [("V1", "00:01:15"), ("V2", "00:05:00")]
    videos = {"V1": "/path/to/V1.txt", "V2": "/path/to/V2.txt"}
    assert build_lines(timestamps, videos) == [
        ("/path/to/V1.txt", "00:01:15", "00:01:25"),
        ("/path/to/V2.txt", "00:05:00", "00:05:10"),
    ]


def test_save_csv(tmp_path):
    lines = [
        ("/path/to/V1.txt", "00:01:15", "00:01:25"),
        ("/path/to/V2.txt", "00:05:00", "00:05:10"),
    ]
    save_csv(lines, tmp_path)
    amanda_csv = tmp_path / "amanda.csv"
    csv_contents = open(amanda_csv, "r").readlines()
    assert csv_contents == [
        "filepath,start,end\n",
        "/path/to/V1.txt,00:01:15,00:01:25\n",
        "/path/to/V2.txt,00:05:00,00:05:10\n",
    ]

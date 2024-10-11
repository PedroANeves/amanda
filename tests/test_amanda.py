# false positive workaround for W0621:redefined-outer-name :
# https://github.com/pylint-dev/pylint/issues/6531
# pylint: disable=redefined-outer-name
import pytest
from docx import Document  # type: ignore

from src.amanda import (
    EN_DASH,
    Row,
    _add_time_delta,
    _extract_name_and_timestamp,
    _has_timestamp,
    _normalize_path,
    build_lines,
    extract_rows,
    extract_timestamps,
    find_file,
    format_lines,
    format_lines_with_header,
)

EXAMPLE_LINES = [
    Row(
        "Remember when the cool thing happened?",
        "V1 00:01:15 – Cool thing happened.",
    ),
    Row("This line should be ignored,", "Because there is no timestamp here"),
    Row(
        "Images dont have timestamps",
        "J1",
    ),
    Row(
        "And then other thing happened.",
        "V2 00:05:00 – Other thing.",
    ),
    Row(
        "Multiple Videos on multiline.",
        "V7 00:00:51 – defesa do Carlos\nV7 00:01:42 – defesa do Carlos",
    ),
    Row(
        "Multiple Images on line",
        "J2 and J3",
    ),
    Row(
        "Mixed images and videos.",
        "J4\nV3 00:00:10 – Description",
    ),
]


@pytest.fixture
def doc(tmp_path):
    filename = tmp_path / "times.docx"
    document = Document()

    table = document.add_table(rows=0, cols=2)
    for comment, times in EXAMPLE_LINES:
        cells = table.add_row().cells
        cells[0].text = comment
        cells[1].text = times

    document.save(filename)
    return filename


def test_extract_rows(doc):
    assert extract_rows(doc) == EXAMPLE_LINES


def test_extract_timestamps():
    assert extract_timestamps(EXAMPLE_LINES) == [
        ("V1", "00:01:15"),
        ("J1", "00:00:00"),
        ("V2", "00:05:00"),
        ("V7", "00:00:51"),
        ("V7", "00:01:42"),
        ("J2", "00:00:00"),
        ("J3", "00:00:00"),
        ("J4", "00:00:00"),
        ("V3", "00:00:10"),
    ]


def test__extract_name_and_timestamp():
    assert _extract_name_and_timestamp(
        "V1 00:01:15 – Cool thing happened."
    ) == [("V1", "00:01:15")]
    assert _extract_name_and_timestamp("J1 – Images dont have timestamps") == [
        ("J1", "00:00:00")
    ]


def test__has_timestamp():
    assert _has_timestamp("V1 00:01:15 – Cool thing happened.")
    assert _has_timestamp("J1 – Cool thing happened.")


@pytest.mark.parametrize(
    "line",
    [
        "This line should be ignored,",
        f"FONTES CONSULTADAS: IMAGENS: {EN_DASH}",
    ],
)
def test_not_has_timestamp(line):
    assert not _has_timestamp(line)


def test_normalize_path():
    assert _normalize_path(r"\path\to\file.txt") == "/path/to/file.txt"


def test_find_file(tmp_path):
    v1_file = tmp_path / "V1 file.txt"
    v1_file.touch()
    n_file = tmp_path / "not a propper file.txt"
    n_file.touch()
    v2_file = tmp_path / "V2 file.txt"
    v2_file.touch()
    j1_file = tmp_path / "J1 file.txt"
    j1_file.touch()

    assert find_file(tmp_path) == {
        "V1": str(v1_file),
        "V2": str(v2_file),
        "J1": str(j1_file),
    }


def test__add_time_delta():
    assert _add_time_delta("00:01:15", 10) == "00:01:25"
    assert _add_time_delta("00:01:15", 15) == "00:01:30"


def test_build_lines():
    timestamps = [("V1", "00:01:15"), ("V2", "00:05:00"), ("J1", "00:05:00")]
    videos = {
        "V1": "/path/to/V1.txt",
        "V2": "/path/to/V2.txt",
        "J1": "/path/to/J1.txt",
    }
    assert build_lines(timestamps, videos) == [
        ("/path/to/V1.txt", "00:01:15", "00:01:25"),
        ("/path/to/V2.txt", "00:05:00", "00:05:10"),
        ("/path/to/J1.txt", "00:05:00", "00:05:10"),
    ]


def test_format_lines():
    lines = [
        ("filepath1", "start1", "end1"),
        ("filepath2", "start2", "end2"),
        ("filepath3", "start3", "end3"),
    ]
    assert format_lines(lines) == [
        "filepath1,start1,end1\n",
        "filepath2,start2,end2\n",
        "filepath3,start3,end3\n",
    ]


def test_format_lines_with_header():
    lines = [
        ("filepath1", "start1", "end1"),
        ("filepath2", "start2", "end2"),
        ("filepath3", "start3", "end3"),
    ]
    assert format_lines_with_header(lines) == [
        "filepath,start,end\n",
        "filepath1,start1,end1\n",
        "filepath2,start2,end2\n",
        "filepath3,start3,end3\n",
    ]

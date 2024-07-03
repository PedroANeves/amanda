# false positive workaround for W0621:redefined-outer-name :
# https://github.com/pylint-dev/pylint/issues/6531
# pylint: disable=redefined-outer-name
import pytest
from docx import Document

from src.amanda import extract_rows


@pytest.fixture
def doc(tmp_path):
    filename = tmp_path / "times.docx"
    document = Document()

    table = document.add_table(rows=0, cols=2)
    lines = [
        (
            "Remember when the cool thing happened?",
            "V1 00:01:15 – Cool thing happened.",
        ),
    ]
    for comment, times in lines:
        cells = table.add_row().cells
        cells[0].text = comment
        cells[1].text = times

    document.save(filename)
    return filename


def test_extract_rows(doc):
    assert extract_rows(doc) == [
        (
            "Remember when the cool thing happened?",
            "V1 00:01:15 – Cool thing happened.",
        ),
    ]

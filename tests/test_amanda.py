# false positive workaround for W0621:redefined-outer-name :
# https://github.com/pylint-dev/pylint/issues/6531
# pylint: disable=redefined-outer-name
import pytest

from src.amanda import extract_rows


@pytest.fixture
def doc():
    return "doc"


def test_extract_rows():
    assert extract_rows(doc) == [
        ("Cool thing happened.", "V1 00:01:15"),
    ]

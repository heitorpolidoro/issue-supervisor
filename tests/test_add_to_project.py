import pytest

from src.app import add_to_project


def test_not_implemented():
    with pytest.raises(NotImplementedError):
        add_to_project(None)

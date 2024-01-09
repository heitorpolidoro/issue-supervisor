from unittest.mock import patch

from src.app import handle_create_or_edit
from tests.conftest import event


def test_handle_create_or_edit(event):
    with (
        patch("src.app.handle_tasklist") as handle_tasklist,
        patch("src.app.add_to_project") as add_to_project,
    ):
        handle_create_or_edit(event)
        handle_tasklist.assert_called_once_with(event)
        add_to_project.assert_called_once_with(event)


def test_handle_create_or_edit_when_issue_has_no_body(event, issue):
    issue.body = None
    with (
        patch("src.app.handle_tasklist") as handle_tasklist,
        patch("src.app.add_to_project") as add_to_project,
    ):
        handle_create_or_edit(event)
        handle_tasklist.assert_not_called()
        add_to_project.assert_called_once_with(event)

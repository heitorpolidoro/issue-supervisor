from unittest.mock import ANY, patch

import pytest

from src.app import handle_tasklist

GET_TASKLIST = "src.app.get_tasklist"
GET_REPOSITORY = "src.app.get_repository"


@pytest.fixture(autouse=True)
def get_issue_mock():
    with patch("src.app.get_issue", return_value=None) as get_issue:
        yield get_issue


def test_create_in_same_repository_with_other_title(event, issue, repository):
    with patch(GET_TASKLIST, return_value=[(False, "local")]), patch(
        GET_REPOSITORY, return_value=None
    ):
        handle_tasklist(event)
        repository.create_issue.assert_called_once_with(title="local")


def test_create_in_other_repository_with_same_title(event, issue, repository):
    with patch(GET_TASKLIST, return_value=[(False, "other_repo")]), patch(
        GET_REPOSITORY, return_value=repository
    ) as get_repository:
        handle_tasklist(event)
        get_repository.assert_called_once_with(ANY, "other_repo")
        repository.create_issue.assert_called_once_with(title="issue title")


def test_create_in_other_repository_with_other_title(event, issue, repository):
    with patch(GET_TASKLIST, return_value=[(False, "[other_repo] other title")]), patch(
        GET_REPOSITORY, return_value=repository
    ) as get_repository:
        handle_tasklist(event)
        get_repository.assert_called_once_with(ANY, "other_repo")
        repository.create_issue.assert_called_once_with(title="other title")


def test_handle_issue_state(event):
    with (
        patch(GET_TASKLIST, return_value=[(True, "repo#issue")]),
        patch("src.app.get_issue", return_value="issue"),
        patch("src.app.handle_issue_state") as handle_issue_state,
    ):
        handle_tasklist(event)
        handle_issue_state.assert_called_once_with(True, "issue")

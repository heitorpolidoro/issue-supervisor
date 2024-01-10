from src.app import get_issue


def test_same_repository_issue(event, repository):
    assert get_issue(event.gh, repository, "#123") is not None
    repository.get_issue.assert_called_once_with(123)


def test_other_repository_issue(event, repository):
    gh = event.gh
    assert get_issue(gh, repository, "owner/other_repository#123") is not None
    gh.get_repo.assert_called_once_with("owner/other_repository")
    gh.get_repo.return_value.get_issue.assert_called_once_with(123)


def test_not_an_issue(event, repository):
    gh = event.gh
    assert get_issue(gh, repository, "not an issue") is None
    gh.get_repo.assert_not_called()

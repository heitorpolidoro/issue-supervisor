"""
This file contains the main application logic for the Pull Request Generator,
including a webhook handler for creating pull requests when new branches are created.
"""
import logging
import os
import re
import sys
from typing import Optional, Union

import sentry_sdk
from flask import Flask
from github import Github, UnknownObjectException
from github.Issue import Issue
from github.Repository import Repository
from githubapp import webhook_handler
from githubapp.events import IssueOpenedEvent, IssuesEvent
from githubapp.events.issues import IssueEditedEvent

logging.basicConfig(
    stream=sys.stdout,
    format="%(levelname)s:%(module)s:%(funcName)s:%(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

if sentry_dns := os.getenv("SENTRY_DSN"):  # pragma: no cover
    # Initialize Sentry SDK for error logging
    sentry_sdk.init(
        dsn=sentry_dns,
        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for performance monitoring.
        traces_sample_rate=1.0,
        # Set profiles_sample_rate to 1.0 to profile 100%
        # of sampled transactions.
        # We recommend adjusting this value in production.
        profiles_sample_rate=1.0,
    )
    logger.info("Sentry initialized")

app = Flask("Issue Supervisor")
app.__doc__ = "This is a Flask application synchronize Github Issues."

webhook_handler.handle_with_flask(app)


def get_repository(
    gh: Github, repository_name: str, repository_owner_login: str = None
) -> Optional[Repository]:
    try:
        return gh.get_repo(repository_name)
    except UnknownObjectException:
        if repository_owner_login:
            return get_repository(gh, f"{repository_owner_login}/{repository_name}")
        return None


def issue_ref(created_issue):
    return f"{created_issue.repository.full_name}#{created_issue.number}"


# def get_issues_to_create(event):
#     gh = event.gh
#     repository = event.repository
#     repository_owner_login = repository.owner.login
#     issue = tests.conftest.issue
#     issue_body = issue.body
#     if not issue_body:
#         return
#
#     for item in re.findall(r"- \[.] ([^\r]*)", issue_body):
#         if re.match(r".*#\d+", item):
#             # Ignoring already created issues
#             continue
#         title = issue.title
#         issue_repository = None
#         if repository_with_title := re.match(r"\[(.+?)] (.+)", item):
#             repository_name, title = repository_with_title.groups()
#             issue_repository = get_repository(
#                 gh, repository_name, repository_owner_login
#             )
#
#         if not issue_repository:
#             issue_repository = get_repository(gh, item, repository_owner_login)
#         if not issue_repository:
#             issue_repository = repository
#             title = item
#
#         created_issue = issue_repository.create_issue(title=title)
#         issue_body = issue_body.replace(item, issue_ref(created_issue))
#     if issue_body != issue.body:
#         issue.edit(body=issue_body)


def get_tasklist(issue_body: str) -> list[tuple[bool, str]]:
    tasks = []
    for line in issue_body.split("\n"):
        if task := re.match(r"- \[(.)] (.*)", line):
            tasks.append((task.group(1) == "x", task.group(2)))
    return tasks


def get_issue(gh: Github, repository: Repository, task: str) -> Optional[Issue]:
    issue_repository, issue_number = task.split("#")
    if issue_repository:
        repository = gh.get_repo(issue_repository)
    return repository.get_issue(int(issue_number))


def add_to_project(event):
    """
    TODO: add to project.
    :param event: 
    :return: 
    """ ""
    raise NotImplementedError()


@webhook_handler.webhook_handler(IssueOpenedEvent)
@webhook_handler.webhook_handler(IssueEditedEvent)
def handle_create_or_edit(event: Union[IssueOpenedEvent, IssueEditedEvent]):
    handle_tasklist(event)
    add_to_project(event)

    # get_issues_to_create(event)


def handle_issue_state(checked, task_issue):
    if checked:
        if task_issue.state == "open":
            task_issue.edit(state="closed")
    elif task_issue.state == "closed":
        task_issue.edit(state="open")


def handle_tasklist(event: IssuesEvent):
    gh = event.gh
    repository = event.repository
    issue = event.issue
    issue_body = issue.body
    for checked, task in get_tasklist(issue_body):
        if task_issue := get_issue(gh, repository, task):
            handle_issue_state(checked, task_issue)

        else:
            if repository_and_title := re.match(r"\[(.+?)] (.+)", task):
                repository_name = repository_and_title.group(1)
                title = repository_and_title.group(2)
            else:
                repository_name = task
                title = issue.title

            if not (issue_repository := get_repository(gh, repository_name)):
                issue_repository = repository
                title = task
            created_issue = issue_repository.create_issue(title=title)
            issue_body = issue_body.replace(task, issue_ref(created_issue))
    if issue_body != issue.body:
        issue.edit(body=issue_body)

# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

import pytest
from pytest_django.fixtures import django_db_setup

from plane.db.models import Issue, Project, State, User, Workspace, WorkspaceMember
from plane.spd.plugins.ticket_guard import service


@pytest.fixture(scope="session")
def django_db_setup(django_db_setup):  # noqa: F811
    pass


@pytest.fixture
def spd_user(db):
    return User.objects.create(email="spd-tests@plane.so", username="spd-tests", first_name="SPD", last_name="Tests")


@pytest.fixture
def spd_workspace(spd_user):
    workspace = Workspace.objects.create(name="SPD", slug="spd-tests", owner=spd_user)
    WorkspaceMember.objects.create(workspace=workspace, member=spd_user, role=20)
    return workspace


@pytest.fixture
def spd_project(spd_workspace, spd_user):
    project = Project.objects.create(name="Suporte", identifier="SUPORTE", workspace=spd_workspace)
    State.objects.create(name="Backlog", color="#000000", project=project, workspace=spd_workspace, default=True)
    return project


@pytest.fixture
def spd_issue(spd_project, spd_workspace, monkeypatch):
    # Created while the plugin is disabled so the receiver stays quiet.
    monkeypatch.delenv("SPD_TICKET_GUARD_PROJECTS", raising=False)
    return Issue.objects.create(
        name="erro",
        description_html="<p>não funciona</p>",
        project=spd_project,
        workspace=spd_workspace,
    )


@pytest.fixture
def guard_enabled(monkeypatch):
    monkeypatch.setenv("SPD_TICKET_GUARD_PROJECTS", "suporte")
    monkeypatch.setenv("SPD_TICKET_GUARD_DEBOUNCE_SECONDS", "0")


class FakeRedis:
    def __init__(self):
        self.store = {}

    def set(self, key, value, ex=None):
        self.store[key] = value

    def get(self, key):
        return self.store.get(key)


@pytest.fixture
def fake_redis(monkeypatch):
    redis = FakeRedis()
    monkeypatch.setattr(service, "redis_instance", lambda: redis)
    return redis


@pytest.fixture
def activity_calls(monkeypatch):
    calls = []
    monkeypatch.setattr(service.issue_activity, "delay", lambda **kwargs: calls.append(kwargs))
    return calls


@pytest.fixture
def scheduled(monkeypatch):
    """Capture review_ticket.apply_async calls."""
    from plane.spd.plugins.ticket_guard import tasks

    calls = []
    monkeypatch.setattr(tasks.review_ticket, "apply_async", lambda **kwargs: calls.append(kwargs))
    return calls

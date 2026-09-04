# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

from celery import shared_task

from plane.db.models import Issue
from plane.spd.plugins.ticket_guard import service


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=2)
def review_ticket(self, issue_id: str, token: str | None = None, force: bool = False):
    """Debounced entry point scheduled by the post_save receiver (or the management command)."""
    if token is not None and not service.is_latest_token(issue_id, token):
        return "superseded"

    issue = Issue.objects.filter(pk=issue_id).select_related("project", "workspace").first()
    if issue is None:
        return "missing"
    if not force and not service.should_review(issue):
        return "skipped"

    review, status = service.review_issue(issue, force=force)
    return status

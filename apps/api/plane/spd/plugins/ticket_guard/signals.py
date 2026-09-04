# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

from django.db import transaction
from django.db.models.signals import post_save

from plane.db.models import Issue
from plane.spd.plugins.ticket_guard import service

DISPATCH_UID = "spd_ticket_guard_issue_post_save"

# Saves that do not touch these fields never need a new review. This also
# ignores the `issue.save(update_fields=["updated_at"])` done by the core
# issue_activity task, which would otherwise re-trigger us after every review.
CONTENT_FIELDS = frozenset({"name", "description_html", "description_stripped", "description_json"})


def connect() -> None:
    post_save.connect(on_issue_saved, sender=Issue, dispatch_uid=DISPATCH_UID)


def disconnect() -> None:
    post_save.disconnect(sender=Issue, dispatch_uid=DISPATCH_UID)


def on_issue_saved(sender, instance, created=False, update_fields=None, raw=False, **kwargs):
    if raw:
        return
    if update_fields is not None and not (CONTENT_FIELDS & set(update_fields)):
        return
    if not service.should_review(instance):
        return
    issue_id = instance.id
    transaction.on_commit(lambda: service.schedule_review(issue_id))

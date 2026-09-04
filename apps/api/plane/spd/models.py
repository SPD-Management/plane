# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

from django.db import models

from plane.db.models.base import BaseModel


class TicketReview(BaseModel):
    """Latest AI review of a work item made by the ticket_guard plugin."""

    workspace = models.ForeignKey("db.Workspace", on_delete=models.CASCADE, related_name="spd_ticket_reviews")
    project = models.ForeignKey("db.Project", on_delete=models.CASCADE, related_name="spd_ticket_reviews")
    issue = models.OneToOneField("db.Issue", on_delete=models.CASCADE, related_name="spd_ticket_review")
    comment = models.ForeignKey(
        "db.IssueComment",
        on_delete=models.SET_NULL,
        related_name="spd_ticket_reviews",
        null=True,
        blank=True,
    )
    content_hash = models.CharField(max_length=64)
    is_valid = models.BooleanField(default=False)
    score = models.IntegerField(null=True, blank=True)
    kind = models.CharField(max_length=32, blank=True, default="")
    problems = models.JSONField(default=list, blank=True)
    suggestion = models.TextField(blank=True, default="")
    raw_response = models.TextField(blank=True, default="")
    model = models.CharField(max_length=255, blank=True, default="")
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Ticket Review"
        verbose_name_plural = "Ticket Reviews"
        db_table = "spd_ticket_reviews"
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.issue_id} valid={self.is_valid} score={self.score}"

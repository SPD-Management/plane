# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

"""
Re-run the Ticket Guard review on one work item, synchronously.

    python manage.py spd_ticket_guard_review SUPORTE-12
    python manage.py spd_ticket_guard_review <issue uuid> --force
"""

import uuid

from django.core.management.base import BaseCommand, CommandError

from plane.db.models import Issue
from plane.spd.plugins.ticket_guard import service


class Command(BaseCommand):
    help = "Review a work item with the Ticket Guard plugin (synchronously)."

    def add_arguments(self, parser):
        parser.add_argument("issue", help="Work item as IDENTIFIER-SEQUENCE (e.g. SUPORTE-12) or UUID")
        parser.add_argument("--force", action="store_true", help="Review even if the content hash is unchanged")
        parser.add_argument(
            "--ignore-project-filter",
            action="store_true",
            help="Review even if the project is not listed in SPD_TICKET_GUARD_PROJECTS",
        )

    def handle(self, *args, **options):
        issue = self._resolve(options["issue"])
        if not options["ignore_project_filter"] and not service.should_review(issue):
            raise CommandError(
                f"{issue.project.identifier}-{issue.sequence_id} is not eligible "
                "(check SPD_TICKET_GUARD_PROJECTS, draft/archived state) — use --ignore-project-filter to override"
            )

        review, status = service.review_issue(issue, force=options["force"])
        self.stdout.write(f"{issue.project.identifier}-{issue.sequence_id}: {status}")
        if review is not None:
            self.stdout.write(f"  valid={review.is_valid} score={review.score} kind={review.kind}")
            for problem in review.problems:
                self.stdout.write(f"  - {problem}")
            if review.suggestion:
                self.stdout.write(f"  suggestion: {review.suggestion}")

    @staticmethod
    def _resolve(ref: str) -> Issue:
        qs = Issue.objects.select_related("project", "workspace")
        try:
            return qs.get(pk=uuid.UUID(ref))
        except ValueError:
            pass
        except Issue.DoesNotExist:
            raise CommandError(f"No work item with id {ref}")

        identifier, _, sequence = ref.rpartition("-")
        if not identifier or not sequence.isdigit():
            raise CommandError("Expected IDENTIFIER-SEQUENCE (e.g. SUPORTE-12) or a UUID")
        issue = qs.filter(project__identifier__iexact=identifier, sequence_id=int(sequence)).first()
        if issue is None:
            raise CommandError(f"No work item {ref}")
        return issue

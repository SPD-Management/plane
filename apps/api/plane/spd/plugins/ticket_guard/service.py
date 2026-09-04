# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

"""
Business logic of the ticket_guard plugin.

Everything here runs as the "Ticket Guard" bot user and never saves the Issue
row itself, so the post_save receiver is never re-triggered by our own writes.
"""

import hashlib
import html
import json
import logging
import uuid
from dataclasses import dataclass, field
from pathlib import Path

from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.db import transaction
from django.utils import timezone

from plane.app.serializers import IssueCommentSerializer
from plane.bgtasks.issue_activities_task import issue_activity
from plane.db.models import Issue, IssueComment, IssueLabel, Label, Project
from plane.settings.redis import redis_instance
from plane.spd import conf, llm
from plane.spd.bot import get_or_create_bot_user
from plane.spd.models import TicketReview
from plane.utils.content_validator import validate_html_content
from plane.utils.exception_logger import log_exception

logger = logging.getLogger("plane.worker")

SOURCE = "spd_ticket_guard"
LABEL_COLOR = "#ef4444"
RULES_DIR = Path(__file__).resolve().parent / "rules"
MAX_DESCRIPTION_CHARS = 12000

OUTPUT_SPEC = """
Responda SOMENTE com um objeto JSON (sem markdown, sem texto fora do JSON) neste formato:
{
  "valid": true | false,
  "score": 0-100,
  "kind": "bug" | "request" | "unknown",
  "problems": ["problema 1", "problema 2"],
  "suggestion": "o que o autor deve acrescentar ou corrigir, em 1-3 frases"
}
"score" mede o quanto o ticket segue o formato (100 = completo). "problems" deve
estar vazio quando o ticket é válido. Escreva em português do Brasil.
"""


@dataclass
class ReviewResult:
    valid: bool
    score: int | None = None
    kind: str = "unknown"
    problems: list[str] = field(default_factory=list)
    suggestion: str = ""
    raw: str = ""
    model: str = ""


# --------------------------------------------------------------------------- #
# Eligibility, debounce and dedupe
# --------------------------------------------------------------------------- #


def _token_key(issue_id) -> str:
    return f"spd:tg:latest:{issue_id}"


def should_review(issue: Issue) -> bool:
    identifiers = conf.ticket_guard_projects()
    if not identifiers:
        return False
    if issue.is_draft or issue.archived_at is not None or issue.deleted_at is not None:
        return False
    return Project.objects.filter(pk=issue.project_id, identifier__in=identifiers).exists()


def schedule_review(issue_id, *, force: bool = False) -> str | None:
    """Register a fresh debounce token and enqueue the review task."""
    from plane.spd.plugins.ticket_guard.tasks import review_ticket

    token = uuid.uuid4().hex
    try:
        redis_instance().set(_token_key(issue_id), token, ex=3600)
    except Exception as e:  # noqa: BLE001 - Redis down must not block the save
        log_exception(e, warning=True)
        token = None

    review_ticket.apply_async(
        args=(str(issue_id), token),
        kwargs={"force": force},
        countdown=conf.ticket_guard_debounce_seconds(),
    )
    return token


def is_latest_token(issue_id, token: str) -> bool:
    try:
        current = redis_instance().get(_token_key(issue_id))
    except Exception as e:  # noqa: BLE001
        log_exception(e, warning=True)
        return True
    if current is None:
        return True
    if isinstance(current, bytes):
        current = current.decode()
    return current == token


def content_hash(issue: Issue) -> str:
    payload = f"{issue.name or ''}\n{issue.description_stripped or ''}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


# --------------------------------------------------------------------------- #
# Prompting
# --------------------------------------------------------------------------- #


def load_rules(project: Project) -> str:
    for name in (f"{project.identifier}.md", "default.md"):
        path = RULES_DIR / name
        if path.is_file():
            return path.read_text(encoding="utf-8")
    raise FileNotFoundError(f"No rules file found in {RULES_DIR}")


def build_system_prompt(project: Project) -> str:
    return f"{load_rules(project).strip()}\n\n{OUTPUT_SPEC.strip()}"


def build_user_prompt(issue: Issue) -> str:
    description = (issue.description_stripped or "").strip()
    if len(description) > MAX_DESCRIPTION_CHARS:
        description = description[:MAX_DESCRIPTION_CHARS] + "\n[... descrição truncada ...]"
    return (
        f"Projeto: {issue.project.identifier}\n"
        f"Ticket: {issue.project.identifier}-{issue.sequence_id}\n"
        f"Título: {issue.name}\n\n"
        f"Descrição:\n{description or '(vazia)'}"
    )


def evaluate(issue: Issue) -> tuple[ReviewResult | None, str | None]:
    """Ask the LLM. Returns (result, None) or (None, error)."""
    data, error, model, raw = llm.complete_json(build_system_prompt(issue.project), build_user_prompt(issue))
    if error:
        return None, error

    score = data.get("score")
    try:
        score = max(0, min(100, int(score))) if score is not None else None
    except (TypeError, ValueError):
        score = None

    problems = data.get("problems") or []
    if not isinstance(problems, list):
        problems = [str(problems)]
    problems = [str(p).strip() for p in problems if str(p).strip()]

    kind = str(data.get("kind") or "unknown").lower()
    if kind not in ("bug", "request", "unknown"):
        kind = "unknown"

    model_valid = bool(data.get("valid"))
    valid = model_valid and (score is None or score >= conf.ticket_guard_min_score())

    return (
        ReviewResult(
            valid=valid,
            score=score,
            kind=kind,
            problems=problems,
            suggestion=str(data.get("suggestion") or "").strip(),
            raw=raw,
            model=model,
        ),
        None,
    )


# --------------------------------------------------------------------------- #
# Applying the verdict
# --------------------------------------------------------------------------- #


def _p(text: str) -> str:
    return f"<p>{html.escape(text)}</p>"


def build_comment_html(result: ReviewResult) -> str:
    if result.valid:
        return "<p><strong>✅ Ticket Guard</strong> — o ticket está no formato esperado.</p>"

    score = f" (pontuação {result.score}/100)" if result.score is not None else ""
    parts = [f"<p><strong>⚠️ Ticket Guard</strong> — o ticket não está no formato esperado{score}.</p>"]
    if result.problems:
        items = "".join(f"<li>{html.escape(p)}</li>" for p in result.problems)
        parts.append(f"<ul>{items}</ul>")
    if result.suggestion:
        parts.append(_p(f"Sugestão: {result.suggestion}"))
    parts.append(_p("Edite o ticket seguindo o template do projeto; ele será reavaliado automaticamente."))
    return "".join(parts)


def _sanitize(comment_html: str) -> str:
    is_valid, _error, clean = validate_html_content(comment_html)
    if not is_valid:
        raise ValueError("Generated comment HTML failed validation")
    return clean if clean is not None else comment_html


def _get_or_create_label(issue: Issue, bot) -> Label:
    name = conf.ticket_guard_label()
    label = Label.objects.filter(project_id=issue.project_id, name=name).first()
    if label is None:
        label = Label(
            project_id=issue.project_id,
            workspace_id=issue.workspace_id,
            name=name,
            color=LABEL_COLOR,
            description="Adicionada automaticamente pelo Ticket Guard",
            external_source=SOURCE,
        )
        label.save(created_by_id=bot.id)
    return label


def _emit(activity_type, *, issue, bot, requested_data, current_instance, notification):
    issue_activity.delay(
        type=activity_type,
        requested_data=requested_data,
        current_instance=current_instance,
        actor_id=str(bot.id),
        issue_id=str(issue.id),
        project_id=str(issue.project_id),
        epoch=int(timezone.now().timestamp()),
        notification=notification,
        origin=settings.WEB_URL,
    )


def apply_result(issue: Issue, result: ReviewResult, *, hash_value: str | None = None) -> TicketReview:
    """Persist label, comment and TicketReview for a verdict; emit activities afterwards."""
    activities: list[dict] = []

    with transaction.atomic():
        bot = get_or_create_bot_user(issue.workspace, issue.project)
        label = _get_or_create_label(issue, bot)

        # ---- label ------------------------------------------------------- #
        current_label_ids = [str(i) for i in IssueLabel.objects.filter(issue=issue).values_list("label_id", flat=True)]
        has_label = str(label.id) in current_label_ids
        new_label_ids = list(current_label_ids)

        if not result.valid and not has_label:
            IssueLabel(issue=issue, label=label, project_id=issue.project_id, workspace_id=issue.workspace_id).save(
                created_by_id=bot.id
            )
            new_label_ids.append(str(label.id))
        elif result.valid and has_label:
            IssueLabel.objects.filter(issue=issue, label=label).delete()
            new_label_ids.remove(str(label.id))

        if new_label_ids != current_label_ids:
            activities.append(
                {
                    "activity_type": "issue.activity.updated",
                    "requested_data": json.dumps({"label_ids": new_label_ids}),
                    "current_instance": json.dumps({"label_ids": current_label_ids}),
                    "notification": False,
                }
            )

        # ---- comment (single, upserted) ---------------------------------- #
        comment = IssueComment.objects.filter(issue=issue, external_source=SOURCE, external_id=str(issue.id)).first()
        comment_html = _sanitize(build_comment_html(result))

        if comment is None:
            if not result.valid:
                comment = IssueComment(
                    issue=issue,
                    project_id=issue.project_id,
                    workspace_id=issue.workspace_id,
                    actor=bot,
                    comment_html=comment_html,
                    external_source=SOURCE,
                    external_id=str(issue.id),
                )
                comment.save(created_by_id=bot.id)
                activities.append(
                    {
                        "activity_type": "comment.activity.created",
                        "requested_data": json.dumps(IssueCommentSerializer(comment).data, cls=DjangoJSONEncoder),
                        "current_instance": None,
                        "notification": True,
                    }
                )
        elif comment.comment_html != comment_html:
            current_instance = json.dumps(IssueCommentSerializer(comment).data, cls=DjangoJSONEncoder)
            comment.comment_html = comment_html
            comment.edited_at = timezone.now()
            comment.updated_by_id = bot.id
            comment.save(disable_auto_set_user=True)
            activities.append(
                {
                    "activity_type": "comment.activity.updated",
                    "requested_data": json.dumps(IssueCommentSerializer(comment).data, cls=DjangoJSONEncoder),
                    "current_instance": current_instance,
                    "notification": not result.valid,
                }
            )

        # ---- review record ----------------------------------------------- #
        review, _created = TicketReview.objects.update_or_create(
            issue=issue,
            defaults={
                "workspace_id": issue.workspace_id,
                "project_id": issue.project_id,
                "comment": comment,
                "content_hash": hash_value or content_hash(issue),
                "is_valid": result.valid,
                "score": result.score,
                "kind": result.kind,
                "problems": result.problems,
                "suggestion": result.suggestion,
                "raw_response": result.raw,
                "model": result.model,
                "reviewed_at": timezone.now(),
            },
        )

    for activity in activities:
        _emit(activity.pop("activity_type"), issue=issue, bot=bot, **activity)

    return review


def review_issue(issue: Issue, *, force: bool = False) -> tuple[TicketReview | None, str]:
    """
    Full pipeline for one issue. Returns (review, status) where status is one of
    "unchanged", "error", "valid", "invalid".
    """
    hash_value = content_hash(issue)
    if not force:
        existing = TicketReview.objects.filter(issue=issue, content_hash=hash_value).first()
        if existing is not None:
            return existing, "unchanged"

    result, error = evaluate(issue)
    if error:
        logger.warning("ticket_guard: LLM review failed for issue %s: %s", issue.id, error)
        return None, "error"

    review = apply_result(issue, result, hash_value=hash_value)
    logger.info(
        "ticket_guard: issue %s reviewed as %s (score=%s, kind=%s)",
        issue.id,
        "valid" if result.valid else "invalid",
        result.score,
        result.kind,
    )
    return review, "valid" if result.valid else "invalid"

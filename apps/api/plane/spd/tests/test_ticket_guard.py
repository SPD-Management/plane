# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

import pytest

from plane.db.models import IssueComment, IssueLabel, Label, ProjectMember, User
from plane.spd import llm
from plane.spd.bot import BOT_TYPE
from plane.spd.models import TicketReview
from plane.spd.plugins.ticket_guard import service, signals
from plane.spd.plugins.ticket_guard.service import ReviewResult
from plane.spd.plugins.ticket_guard.tasks import review_ticket

pytestmark = [pytest.mark.unit, pytest.mark.django_db]


def fake_llm(monkeypatch, data, error=None):
    calls = []

    def _complete(system_prompt, user_prompt):
        calls.append((system_prompt, user_prompt))
        if error:
            return None, error, "fake-model", ""
        return data, None, "fake-model", "{...}"

    monkeypatch.setattr(llm, "complete_json", _complete)
    return calls


INVALID = {
    "valid": False,
    "score": 20,
    "kind": "unknown",
    "problems": ["Tipo não declarado", "Sem passos"],
    "suggestion": "Diga se é bug.",
}
VALID = {"valid": True, "score": 95, "kind": "bug", "problems": [], "suggestion": ""}


# --------------------------------------------------------------------------- #
# llm.parse_json
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "text",
    [
        '{"valid": true, "score": 90}',
        '```json\n{"valid": true, "score": 90}\n```',
        'Claro! Aqui está: {"valid": true, "score": 90} espero ter ajudado',
    ],
)
def test_parse_json_accepts_plain_fenced_and_embedded(text):
    assert llm.parse_json(text) == {"valid": True, "score": 90}


def test_parse_json_rejects_garbage():
    assert llm.parse_json("nope") is None
    assert llm.parse_json("[1, 2]") is None
    assert llm.parse_json("") is None


# --------------------------------------------------------------------------- #
# receiver
# --------------------------------------------------------------------------- #


def test_receiver_ignores_when_no_project_configured(spd_issue, scheduled, fake_redis, monkeypatch):
    monkeypatch.delenv("SPD_TICKET_GUARD_PROJECTS", raising=False)
    signals.on_issue_saved(sender=None, instance=spd_issue)
    assert scheduled == []


def test_receiver_ignores_updated_at_only_saves(spd_issue, scheduled, fake_redis, guard_enabled):
    signals.on_issue_saved(sender=None, instance=spd_issue, update_fields=frozenset({"updated_at"}))
    assert scheduled == []


def test_receiver_ignores_drafts_and_raw(spd_issue, scheduled, fake_redis, guard_enabled):
    signals.on_issue_saved(sender=None, instance=spd_issue, raw=True)
    spd_issue.is_draft = True
    signals.on_issue_saved(sender=None, instance=spd_issue)
    assert scheduled == []


def test_receiver_schedules_with_token_on_content_save(
    spd_issue, scheduled, fake_redis, guard_enabled, django_capture_on_commit_callbacks
):
    with django_capture_on_commit_callbacks(execute=True):
        signals.on_issue_saved(sender=None, instance=spd_issue, update_fields=frozenset({"name", "updated_at"}))
    assert len(scheduled) == 1
    issue_id, token = scheduled[0]["args"]
    assert issue_id == str(spd_issue.id)
    assert fake_redis.store[f"spd:tg:latest:{spd_issue.id}"] == token


def test_real_issue_save_reaches_receiver(
    spd_project, spd_workspace, scheduled, fake_redis, guard_enabled, django_capture_on_commit_callbacks
):
    from plane.db.models import Issue

    with django_capture_on_commit_callbacks(execute=True):
        issue = Issue.objects.create(
            name="x", description_html="<p>y</p>", project=spd_project, workspace=spd_workspace
        )
    assert [c["args"][0] for c in scheduled] == [str(issue.id)]


# --------------------------------------------------------------------------- #
# task
# --------------------------------------------------------------------------- #


def test_task_skips_superseded_token(spd_issue, fake_redis, guard_enabled, monkeypatch):
    calls = fake_llm(monkeypatch, INVALID)
    fake_redis.store[f"spd:tg:latest:{spd_issue.id}"] = "newer"
    assert review_ticket.run(str(spd_issue.id), "older") == "superseded"
    assert calls == []


def test_task_reviews_then_dedupes_by_hash(spd_issue, fake_redis, guard_enabled, activity_calls, monkeypatch):
    calls = fake_llm(monkeypatch, INVALID)
    assert review_ticket.run(str(spd_issue.id), None) == "invalid"
    assert review_ticket.run(str(spd_issue.id), None) == "unchanged"
    assert len(calls) == 1
    assert TicketReview.objects.filter(issue=spd_issue).count() == 1


def test_task_force_bypasses_hash(spd_issue, fake_redis, guard_enabled, activity_calls, monkeypatch):
    calls = fake_llm(monkeypatch, INVALID)
    review_ticket.run(str(spd_issue.id), None)
    review_ticket.run(str(spd_issue.id), None, force=True)
    assert len(calls) == 2


def test_review_error_leaves_no_trace(spd_issue, guard_enabled, activity_calls, monkeypatch):
    fake_llm(monkeypatch, None, error="boom")
    review, status = service.review_issue(spd_issue)
    assert (review, status) == (None, "error")
    assert not TicketReview.objects.filter(issue=spd_issue).exists()
    assert not IssueComment.objects.filter(issue=spd_issue).exists()


# --------------------------------------------------------------------------- #
# apply_result
# --------------------------------------------------------------------------- #


def test_invalid_result_adds_label_comment_and_review(spd_issue, guard_enabled, activity_calls):
    review = service.apply_result(
        spd_issue,
        ReviewResult(valid=False, score=20, problems=["Tipo não declarado"], suggestion="Diga se é bug", model="m"),
    )

    bot = User.objects.get(username=f"spd_ticket_guard_{spd_issue.workspace_id}")
    assert bot.is_bot and bot.bot_type == BOT_TYPE
    assert ProjectMember.objects.filter(project=spd_issue.project, member=bot, is_active=True).exists()

    label = Label.objects.get(project=spd_issue.project, name="formato-invalido")
    assert label.created_by_id == bot.id
    assert IssueLabel.objects.filter(issue=spd_issue, label=label).exists()

    comment = IssueComment.objects.get(issue=spd_issue, external_source=service.SOURCE)
    assert comment.actor_id == bot.id
    assert "Tipo não declarado" in comment.comment_html
    assert "⚠️" in comment.comment_html

    assert review.is_valid is False and review.score == 20 and review.comment_id == comment.id
    assert [c["type"] for c in activity_calls] == ["issue.activity.updated", "comment.activity.created"]
    assert activity_calls[1]["notification"] is True
    assert activity_calls[0]["actor_id"] == str(bot.id)


def test_reapply_upserts_single_comment(spd_issue, guard_enabled, activity_calls):
    service.apply_result(spd_issue, ReviewResult(valid=False, score=20, problems=["A"]))
    service.apply_result(spd_issue, ReviewResult(valid=False, score=30, problems=["B"]))

    comments = IssueComment.objects.filter(issue=spd_issue, external_source=service.SOURCE)
    assert comments.count() == 1
    assert "B" in comments.get().comment_html and comments.get().edited_at is not None
    assert IssueLabel.objects.filter(issue=spd_issue).count() == 1
    assert [c["type"] for c in activity_calls][-1] == "comment.activity.updated"


def test_valid_after_invalid_clears_label_and_marks_comment(spd_issue, guard_enabled, activity_calls):
    service.apply_result(spd_issue, ReviewResult(valid=False, score=20, problems=["A"]))
    service.apply_result(spd_issue, ReviewResult(valid=True, score=95, kind="bug"))

    assert not IssueLabel.objects.filter(issue=spd_issue).exists()
    comment = IssueComment.objects.get(issue=spd_issue, external_source=service.SOURCE)
    assert "✅" in comment.comment_html
    assert TicketReview.objects.get(issue=spd_issue).is_valid is True


def test_valid_first_time_creates_no_comment(spd_issue, guard_enabled, activity_calls):
    service.apply_result(spd_issue, ReviewResult(valid=True, score=95))
    assert not IssueComment.objects.filter(issue=spd_issue).exists()
    assert not IssueLabel.objects.filter(issue=spd_issue).exists()
    assert activity_calls == []


def test_evaluate_applies_min_score(spd_issue, guard_enabled, monkeypatch):
    fake_llm(monkeypatch, {"valid": True, "score": 50, "kind": "bug"})
    monkeypatch.setenv("SPD_TICKET_GUARD_MIN_SCORE", "70")
    result, error = service.evaluate(spd_issue)
    assert error is None and result.valid is False and result.score == 50


def test_comment_html_escapes_model_output():
    html = service.build_comment_html(ReviewResult(valid=False, problems=["<script>x</script>"]))
    assert "<script>" not in html and "&lt;script&gt;" in html

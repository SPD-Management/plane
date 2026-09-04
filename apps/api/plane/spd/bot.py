# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

"""
Bot user used as the author of everything the SPD plugins write.

Follows the pattern of plane.bgtasks.workspace_seed_task: a real User row
with is_bot=True, which the core member listings already filter out.
"""

import uuid
from urllib.parse import urlparse

from django.conf import settings
from django.contrib.auth.hashers import make_password

from plane.db.models import ProjectMember, User, WorkspaceMember

BOT_TYPE = "SPD_TICKET_GUARD"
BOT_DISPLAY_NAME = "Ticket Guard"
MEMBER_ROLE = 15  # ROLE.MEMBER


def _bot_email_domain() -> str:
    return urlparse(settings.WEB_URL or "https://plane.so").hostname or "plane.so"


def get_or_create_bot_user(workspace, project=None) -> User:
    """Return the workspace's Ticket Guard bot, creating it (and its memberships) on first use."""
    username = f"spd_ticket_guard_{workspace.id}"
    bot = User.objects.filter(username=username).first()
    if bot is None:
        bot = User.objects.create(
            username=username,
            display_name=BOT_DISPLAY_NAME,
            first_name=BOT_DISPLAY_NAME,
            last_name="",
            is_bot=True,
            bot_type=BOT_TYPE,
            email=f"{username}@{_bot_email_domain()}",
            password=make_password(uuid.uuid4().hex),
            is_password_autoset=True,
        )

    WorkspaceMember.objects.get_or_create(
        workspace=workspace,
        member=bot,
        defaults={"role": MEMBER_ROLE, "company_role": ""},
    )
    if project is not None:
        ProjectMember.objects.get_or_create(
            workspace=workspace,
            project=project,
            member=bot,
            defaults={"role": MEMBER_ROLE, "is_active": True},
        )
    return bot

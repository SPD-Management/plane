# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

"""
Celery autodiscovery entry point (`app.autodiscover_tasks()` looks for a
`tasks` module in every installed app). Plugin tasks are re-exported here so
they are registered in the worker even before the plugin registry runs.
"""

from plane.spd.plugins.ticket_guard.tasks import review_ticket  # noqa: F401

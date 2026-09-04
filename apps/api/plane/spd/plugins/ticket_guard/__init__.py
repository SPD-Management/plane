# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

"""
ticket_guard: reviews work items of selected projects with an LLM and flags
the ones that do not follow the expected ticket format (bot comment + label).
"""


def register() -> None:
    from plane.spd.plugins.ticket_guard import signals

    signals.connect()

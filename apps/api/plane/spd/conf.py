# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

"""
Environment-driven configuration for the Speedio extension layer.

All values are read at call time (not import time) so tests can monkeypatch
the environment and so a running worker picks up changes after a restart
without any import-order surprises.
"""

import os


def _csv(name: str, default: str = "") -> list[str]:
    raw = os.environ.get(name, default)
    return [item.strip() for item in raw.split(",") if item.strip()]


def _int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


def enabled_plugins() -> list[str]:
    """Plugins to load, by module name under `plane.spd.plugins`."""
    return _csv("SPD_PLUGINS", "ticket_guard")


# --- ticket_guard ---------------------------------------------------------


def ticket_guard_projects() -> list[str]:
    """Project identifiers (e.g. "SUPORTE") whose work items are reviewed."""
    return [identifier.upper() for identifier in _csv("SPD_TICKET_GUARD_PROJECTS")]


def ticket_guard_label() -> str:
    return os.environ.get("SPD_TICKET_GUARD_LABEL", "formato-invalido").strip() or "formato-invalido"


def ticket_guard_debounce_seconds() -> int:
    return max(0, _int("SPD_TICKET_GUARD_DEBOUNCE_SECONDS", 20))


def ticket_guard_min_score() -> int:
    return min(100, max(0, _int("SPD_TICKET_GUARD_MIN_SCORE", 70)))

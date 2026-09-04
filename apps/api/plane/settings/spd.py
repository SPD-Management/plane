# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

"""
Production settings + Speedio extension layer.

Activate with DJANGO_SETTINGS_MODULE=plane.settings.spd on api, worker,
beat-worker and migrator. See docs/spd-extensions.md.
"""

from .production import *  # noqa

INSTALLED_APPS += ("plane.spd",)  # noqa

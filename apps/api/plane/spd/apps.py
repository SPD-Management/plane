# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

from django.apps import AppConfig


class SpdConfig(AppConfig):
    """
    Speedio extension layer.

    Everything fork-specific lives under `plane.spd` so that syncing with the
    upstream repository never touches these files. The app is activated by
    pointing DJANGO_SETTINGS_MODULE at `plane.settings.spd` (or `spd_local`,
    `spd_test`); see docs/spd-extensions.md.
    """

    name = "plane.spd"
    label = "spd"
    verbose_name = "Speedio extensions"

    def ready(self):
        from plane.spd.plugins import load_plugins

        load_plugins()

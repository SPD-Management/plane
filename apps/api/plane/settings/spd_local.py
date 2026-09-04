# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

"""Local development settings + Speedio extension layer."""

from .local import *  # noqa

INSTALLED_APPS += ("plane.spd",)  # noqa

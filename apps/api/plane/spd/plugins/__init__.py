# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

"""
Plugin registry for the SPD extension layer.

A plugin is a package under `plane.spd.plugins` exposing a `register()`
function. Plugins are selected with the SPD_PLUGINS env var (comma-separated
module names) and loaded once from SpdConfig.ready().
"""

import importlib
import logging

from plane.spd import conf

logger = logging.getLogger("plane.worker")

_loaded: set[str] = set()


def load_plugins() -> list[str]:
    for name in conf.enabled_plugins():
        if name in _loaded:
            continue
        try:
            module = importlib.import_module(f"plane.spd.plugins.{name}")
        except ImportError:
            logger.exception("SPD plugin %r could not be imported", name)
            continue
        register = getattr(module, "register", None)
        if callable(register):
            register()
        _loaded.add(name)
        logger.info("SPD plugin %r loaded", name)
    return sorted(_loaded)

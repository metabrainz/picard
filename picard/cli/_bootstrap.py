# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2025 Philipp Wolfer
# Copyright (C) 2025-2026 Laurent Monin
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.

"""Shared bootstrap for Picard CLI commands (picard-cli).

Provides minimal initialization of QCoreApplication and Picard config
without starting the full GUI application.
"""

import logging
import os
import sys

from PyQt6 import QtCore

from picard import (
    PICARD_APP_NAME,
    PICARD_ORG_NAME,
)
from picard.config import setup_config
from picard.options import init_options


def minimal_init(config_file=None, *, with_webservice=False):
    """Minimal initialization for CLI commands without GUI.

    Sets up QCoreApplication, registers options, and loads config.
    Optionally initializes WebService for network operations.

    Args:
        config_file: Path to config file, or None for default location.
        with_webservice: If True, initialize WebService on the app instance.

    Returns:
        QCoreApplication instance (must stay alive for Qt event processing).
    """
    QtCore.QCoreApplication.setApplicationName(PICARD_APP_NAME)
    QtCore.QCoreApplication.setOrganizationName(PICARD_ORG_NAME)

    app = QtCore.QCoreApplication(sys.argv)

    init_options()
    setup_config(app=app, filename=config_file)

    if with_webservice:
        # Import here to avoid circular imports and unnecessary loading
        # when webservice is not needed
        from picard.webservice import WebService

        app.webservice = WebService()

    return app


def init_logging(args):
    """Configure logging for CLI commands.

    Sets up console handler and verbosity based on --debug / --debug-opts flags.

    Args:
        args: Parsed argparse namespace with 'debug' and 'debug_opts' attributes.
    """
    from picard import log
    from picard.debug_opts import DebugOpt

    log.enable_console_handler()

    debug = getattr(args, 'debug', False)
    debug_opts = getattr(args, 'debug_opts', None)

    if not debug and not debug_opts:
        log.set_verbosity(logging.WARNING)
    else:
        log.set_verbosity(logging.DEBUG)

    if debug_opts:
        DebugOpt.from_string(debug_opts)


def is_color_disabled(args):
    """Determine whether colored output should be disabled.

    Checks both the --no-color flag and the NO_COLOR environment variable.

    Args:
        args: Parsed argparse namespace with 'no_color' attribute.

    Returns:
        True if color should be disabled, False otherwise.
    """
    return getattr(args, 'no_color', False) or 'NO_COLOR' in os.environ


def init_cli(args, *, with_webservice=False):
    """Full CLI initialization: app bootstrap + logging + color detection.

    Convenience function combining minimal_init() and init_logging().
    Use this in subcommand handlers instead of calling each step manually.

    Args:
        args: Parsed argparse namespace (must have config_file, debug, debug_opts).
        with_webservice: If True, initialize WebService on the app instance.

    Returns:
        QCoreApplication instance.
    """
    config_file = getattr(args, 'config_file', None)
    app = minimal_init(config_file, with_webservice=with_webservice)
    init_logging(args)
    return app

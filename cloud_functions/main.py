# Copyright 2023 The ChromiumOS Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""Cloud Functions entry point implementations."""

import flask

from lib import secret_manager


def main(request: flask.Request) -> str:
    """Responds to HTTP requests for testing. To be removed/updated."""
    secrets = secret_manager.LookupServiceDbSecrets()
    return secrets.host

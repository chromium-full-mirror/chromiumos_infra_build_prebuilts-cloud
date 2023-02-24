# Copyright 2023 The ChromiumOS Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""Cloud Functions entry point implementations."""

import os

import flask

from lib import db_connector
from lib import secret_manager


def main(request: flask.Request) -> str:
    """Responds to HTTP requests for testing. To be removed/updated."""

    secrets = secret_manager.LookupServiceDbSecrets()
    lookup_service_db_connection = db_connector.LookupServiceDBConnection(
        database=secrets.database_name,
        host=os.environ.get("PREBUILTS_SQL_INSTANCE_HOST"),
        port=os.environ.get("PREBUILTS_SQL_INSTANCE_PORT"),
        username=secrets.user,
        password=secrets.password,
    )

    return secrets.database_name

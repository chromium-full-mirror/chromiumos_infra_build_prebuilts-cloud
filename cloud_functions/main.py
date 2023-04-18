# Copyright 2023 The ChromiumOS Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""Cloud Functions entry point implementations."""


# pylint: disable=import-error
from cloudevents.http.event import CloudEvent
import flask.wrappers
import functions_framework

# pylint: enable=import-error
from lib import config
from lib import db_connector
from lib import secret_manager
from service import update_operations


@functions_framework.http
def lookup_service(
    request: flask.wrappers.Request,  # pylint: disable=unused-argument
) -> str:
    """Responds to HTTP requests for testing. To be removed/updated."""

    secrets = secret_manager.LookupServiceDbSecrets()
    # pylint: disable=unused-variable
    lookup_service_db_connection = db_connector.LookupServiceDBConnection(
        **config.READER.get("lookup_service_db")
    )
    # pylint: enable=unused-variable

    return secrets.database_name


@functions_framework.cloud_event
def update_service(cloud_event: CloudEvent) -> None:
    """Perform update operations based on pubsub messages.

    Entry point for the `update_service` cloud function which has subscriptions
    to different pubsub topics.

    Args:
        cloud_event: Event received from the pubsub subscription, follows format
            of the CloudEvents specification.
    """
    update_operations.process_pubsub_message(cloud_event)

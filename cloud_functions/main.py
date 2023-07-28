# Copyright 2023 The ChromiumOS Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""Cloud Functions entry point implementations."""


# pylint: disable=import-error
from cloudevents.http import event
import flask
import flask.wrappers
import functions_framework

# pylint: enable=import-error
from lib import config
from lib import db_connector
from service import lookup_operations
from service import update_operations


@functions_framework.http
def lookup_service_binhosts(request: flask.wrappers.Request) -> flask.Response:
    """Lookup binhosts based on the filter parameters.

    Entry point for the cloud function which looks up binhosts based on the
    filter parameters and returns their storage locations.

    Args:
        request: Flask request object containing filter parameters to lookup
            binhosts.

    Returns:
        A flask Response object containing a
        `prebuilts_cloud_pb2.LookupBinhostsResponse` object encoded with base64,
        in bytes.
    """
    lookup_service_db_connection = db_connector.LookupServiceDBConnection(
        **config.READER.get("lookup_service_db")
    )

    return lookup_operations.lookup_binhosts(
        request, lookup_service_db_connection
    )


@functions_framework.cloud_event
def update_service(cloud_event: event.CloudEvent) -> None:
    """Perform update operations based on pubsub messages.

    Entry point for the `update_service` cloud function which has subscriptions
    to different pubsub topics.

    Args:
        cloud_event: Event received from the pubsub subscription, follows format
            of the CloudEvents specification.
    """
    update_operations.process_pubsub_message(cloud_event)

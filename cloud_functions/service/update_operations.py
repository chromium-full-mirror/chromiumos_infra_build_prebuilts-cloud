# Copyright 2023 The ChromiumOS Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""Update operations on the `lookup_service` database."""

import base64
from typing import Tuple

from cloudevents.http.event import CloudEvent
from google.protobuf.message import DecodeError
from protobuf.chromiumos import prebuilts_cloud_pb2

from lib import config
from lib import db_connector


class UpdateOperationsError(Exception):
    """Base error class for the module."""


class UnknownTopicError(UpdateOperationsError):
    """Error when the pubsub topic is unknown."""


def _parse_pubsub_msg(cloud_event: CloudEvent) -> Tuple[bytes, str]:
    """Parse cloud_event and return the message data, pub sub topic.

    Args:
        cloud_event: Event received from the pubsub subscription, follows format
            of the CloudEvents specification.

    Returns:
        msg_data: Data in the pub sub message.
        pubsub_topic: Topic the pub sub message belongs to.
    """
    msg_data = base64.b64decode(cloud_event.data["message"]["data"])
    pubsub_topic = cloud_event["source"].split("//pubsub.googleapis.com/")[1]

    return msg_data, pubsub_topic


def process_pubsub_message(cloud_event: CloudEvent) -> None:
    """Process pubsub message and perform corresponding database operations.

    Args:
        cloud_event: Event received from the pubsub subscription, follows format
            of the CloudEvents specification.

    Raises:
       UnknownTopicError: When the received pubsub topic is unknown.
    """
    lookup_service_db_connection = db_connector.LookupServiceDBConnection(
        **config.READER.get("lookup_service_db")
    )

    msg_data, pubsub_topic = _parse_pubsub_msg(cloud_event)

    if pubsub_topic == config.READER.get("topics")["update_snapshot_data"]:
        update_snapshot_data(lookup_service_db_connection, msg_data)
    else:
        raise UnknownTopicError(
            f"Could not process the message due to unknown Pub/Sub topic: "
            f"{pubsub_topic}"
        )


def update_snapshot_data(
    lookup_service_db_connection: db_connector.LookupServiceDBConnection,
    msg_data: bytes,
) -> None:
    """Create or update a snapshot record based on the pub sub message.

    Args:
        lookup_service_db_connection: Connection object to the lookup_service
            database.
        msg_data: Data received in the pubsub message in binary format.

    Raises:
        DBError: When there is database operation error.
        UpdateOperationsError: When there is an error while parsing Pub/Sub
            message data.
    """
    snapshot_data = prebuilts_cloud_pb2.UpdateSnapshotDataRequest()

    try:
        snapshot_data.ParseFromString(msg_data)
    except DecodeError as err:
        raise UpdateOperationsError(
            "Unable to parse snapshot data from Pub/Sub message."
        ) from err

    snapshot_args = {
        "snapshot_sha": snapshot_data.snapshot_sha,
        "snapshot_num": snapshot_data.snapshot_num,
        "external": snapshot_data.external,
        "buildbucket_id": snapshot_data.buildbucket_id,
    }

    existing_snapshot = lookup_service_db_connection.snapshots_read(
        snapshot_data.snapshot_sha, required=False
    )

    if not existing_snapshot:
        lookup_service_db_connection.snapshots_create(**snapshot_args)
    else:
        lookup_service_db_connection.snapshots_update(**snapshot_args)

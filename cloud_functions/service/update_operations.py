# Copyright 2023 The ChromiumOS Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""Update operations on the `lookup_service` database."""

import base64
import logging
import re
from typing import Tuple

# pylint: disable=import-error
from cloudevents.http.event import CloudEvent
from google.protobuf.message import DecodeError
from protobuf.chromiumos import prebuilts_cloud_pb2

# pylint: enable=import-error
from lib import config
from lib import db_connector


# Regex for a Pub/Sub topic name which uniquely identifies a topic, it follows
# the pattern `projects/project-identifier/topics/ID`.
_PUBSUB_TOPIC_NAME_RE = re.compile(
    r"projects\/[a-z][-a-z0-9]{4,28}[a-z0-9]{1}\/topics\/"
    r"[A-Za-z][-A-Za-z0-9._~%+]{2,254}$"
)


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
        pubsub_topic_name: Complete name that uniquely identifies a Pub/Sub
            topic. This is the topic the message belongs to.
    """
    msg_data = base64.b64decode(cloud_event.data["message"]["data"])
    event_source_split = cloud_event["source"].split("//pubsub.googleapis.com/")

    # Check if the event source contains a Pub/Sub topic name.
    if len(event_source_split) == 2 and _PUBSUB_TOPIC_NAME_RE.match(
        event_source_split[1]
    ):
        return msg_data, event_source_split[1]

    raise UpdateOperationsError(
        "Unable to parse a valid Pub/Sub topic name from the event source: "
        f"{cloud_event['source']}."
    )


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

    msg_data, pubsub_topic_name = _parse_pubsub_msg(cloud_event)
    logging.info("Update request for PubSub topic: %s", pubsub_topic_name)
    if pubsub_topic_name == config.READER.get("topics")["update_snapshot_data"]:
        update_snapshot_data(lookup_service_db_connection, msg_data)
    elif (
        pubsub_topic_name == config.READER.get("topics")["update_binhost_data"]
    ):
        update_binhost_data(lookup_service_db_connection, msg_data)
    else:
        raise UnknownTopicError(
            f"Could not process the message due to unknown Pub/Sub topic: "
            f"{pubsub_topic_name}."
        )


def update_snapshot_data(
    lookup_service_db_connection: db_connector.LookupServiceDBConnection,
    msg_data: bytes,
) -> None:
    """Create or update a snapshot record based on the pub sub message.

    Args:
        lookup_service_db_connection: Connection object to the lookup_service
            database.
        msg_data: Data received in the pubsub message in bytes.

    Raises:
        DBError: When there is database operation error.
        UpdateOperationsError: When there is an error while parsing Pub/Sub
            message data.
    """
    snapshot_data = prebuilts_cloud_pb2.UpdateSnapshotDataRequest()
    try:
        snapshot_data.ParseFromString(msg_data)
    except DecodeError as err:
        error_msg = "Unable to parse snapshot data from Pub/Sub message."
        logging.error(error_msg)
        logging.error(err)
        raise UpdateOperationsError(error_msg) from err
    logging.info("Update snapshot data request: \n%s", snapshot_data)
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
        logging.info("Updating existing snapshot record.")
        lookup_service_db_connection.snapshots_create(**snapshot_args)
    else:
        logging.info("Creating new snapshot record.")
        lookup_service_db_connection.snapshots_update(**snapshot_args)


def update_binhost_data(
    lookup_service_db_connection: db_connector.LookupServiceDBConnection,
    msg_data: bytes,
) -> None:
    """Create or update a binhost record based on the pub sub message.

    Create or update binhost records, also update the build target profiles
    table to keep track of all build targets and their associated profiles.

    Args:
        lookup_service_db_connection: Connection object to the lookup_service
            database.
        msg_data: Data received in the pubsub message in bytes.

    Raises:
        DBError: When there is database operation error.
        UpdateOperationsError: When there is an error while parsing Pub/Sub
            message data.
    """
    binhost_data = prebuilts_cloud_pb2.UpdateBinhostDataRequest()

    try:
        binhost_data.ParseFromString(msg_data)
    except DecodeError as err:
        error_message = "Unable to parse binhost data from Pub/Sub message."
        logging.error(error_message)
        logging.error(err)
        raise UpdateOperationsError(error_message) from err

    logging.info("Update binhost data request: \n%s", binhost_data)
    build_target_profiles = (
        lookup_service_db_connection.build_target_profiles_filter(
            (
                f"build_target='{binhost_data.build_target}' AND "
                f"profile='{binhost_data.profile}'"
            ),
            limit=1,
        )
    )

    if build_target_profiles:
        build_target_profile_id = build_target_profiles[
            0
        ].build_target_profile_id
    else:
        created_build_target_profile = (
            lookup_service_db_connection.build_target_profiles_create(
                build_target=binhost_data.build_target,
                profile=binhost_data.profile,
            )
        )
        build_target_profile_id = (
            created_build_target_profile.build_target_profile_id
        )
        logging.info(
            "Created new build_target_profile record with id: %s",
            build_target_profile_id,
        )

    binhost_args = {
        "build_target_profile_id": build_target_profile_id,
        "snapshot_sha": binhost_data.snapshot_sha,
        "gs_uri": binhost_data.gs_uri,
        "gs_bucket_name": binhost_data.gs_bucket_name,
        "buildbucket_id": binhost_data.buildbucket_id,
        "complete": binhost_data.complete,
        "private": binhost_data.private,
    }
    existing_binhosts = lookup_service_db_connection.binhosts_filter(
        f"gs_uri='{binhost_data.gs_uri}'", limit=1
    )
    if existing_binhosts:
        existing_binhost_id = existing_binhosts[0].binhost_id
        lookup_service_db_connection.binhosts_update(
            binhost_id=existing_binhost_id,
            **binhost_args,
        )
        logging.info(
            "Updated existing binhost record with binhost id: %d",
            existing_binhost_id,
        )
    else:
        new_binhost = lookup_service_db_connection.binhosts_create(
            **binhost_args
        )
        logging.info(
            "Created a new binhost record with binhost id: %d",
            new_binhost.binhost_id,
        )

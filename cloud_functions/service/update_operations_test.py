# Copyright 2023 The ChromiumOS Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""Test the update_operations module."""

# Protected access is needed to mock protected members of classes for tests.
# pylint: disable=protected-access

from typing import List
from unittest.mock import Mock

# pylint: disable=import-error
from cloudevents.http.event import CloudEvent
import pytest

# pylint: enable=import-error
from lib import config
from lib import db_connector
from lib import models
from service import update_operations


# Mock data for `update_snapshot_data` msg, it decodes to:
# {'snapshot_sha': 'test_sha', 'snapshot_num': 1, 'external': True,
# 'buildbucket_id': 2}
MOCK_UPDATE_SNAPSHOT_MSG_DATA = b"\n\x08test_sha\x10\x01\x18\x01 \x02"


@pytest.mark.parametrize(
    "event_source, pubsub_topic_name",
    [
        (
            "//pubsub.googleapis.com/projects/test-project/topics/"
            "staging-update_data",
            "projects/test-project/topics/staging-update_data",
        ),
        (
            "//pubsub.googleapis.com/projects/test-project/topics/test_topic",
            "projects/test-project/topics/test_topic",
        ),
    ],
)
def test__parse_pubsub_msg(
    event_source: str, pubsub_topic_name: str, mock_cloud_event: CloudEvent
):
    """Test the _parse_pubsub_msg function with valid inputs."""
    mock_cloud_event._attributes["source"] = event_source

    msg_data, pubsub_topic = update_operations._parse_pubsub_msg(
        mock_cloud_event
    )

    assert msg_data == MOCK_UPDATE_SNAPSHOT_MSG_DATA
    assert pubsub_topic == pubsub_topic_name


@pytest.mark.parametrize(
    "event_source",
    [
        "",
        "//pubsub.googleapis.com/projects/123",
        "//pubsub.googleapis.com/projects/test-project/topics/",
    ],
)
def test__parse_pubsub_msg_error(
    event_source: str, mock_cloud_event: CloudEvent
):
    """Test error handling of the _parse_pubsub_msg function."""
    mock_cloud_event._attributes["source"] = event_source

    # Exception should be raised when a Pub/Sub topic name cannot be parsed.
    with pytest.raises(
        update_operations.UpdateOperationsError,
        match=f"Unable to parse a valid Pub/Sub topic name from the event "
        f"source: {event_source}.",
    ):
        update_operations._parse_pubsub_msg(mock_cloud_event)


def test_process_pubsub_message(
    monkeypatch,
    mock_cloud_event: CloudEvent,
    mock_config_reader: config.ConfigReader,
):
    """Test the function which processes incoming Pub/Sub messages."""
    monkeypatch.setattr(db_connector, "LookupServiceDBConnection", Mock())
    monkeypatch.setattr(config, "READER", mock_config_reader)
    monkeypatch.setattr(update_operations, "update_snapshot_data", Mock())
    monkeypatch.setattr(update_operations, "update_binhost_data", Mock())
    # Overwrite the `source` attribute of the mock cloud event so it can be
    # treated as a Pub/Sub message to update binhost data.
    mock_cloud_event._attributes["source"] = (
        "//pubsub.googleapis.com/projects/test-project/"
        "topics/test_topic_update_binhost_data"
    )

    update_operations.process_pubsub_message(mock_cloud_event)

    update_operations.update_binhost_data.assert_called_once()


def test_process_pubsub_message_error(
    monkeypatch,
    mock_cloud_event: CloudEvent,
    mock_config_reader: config.ConfigReader,
):
    """Test error handling of the process_pubsub_message function."""
    monkeypatch.setattr(db_connector, "LookupServiceDBConnection", Mock())
    monkeypatch.setattr(config, "READER", mock_config_reader)
    # Overwrite the `source` attribute of the mock cloud event to an unkown
    # topic.
    mock_cloud_event._attributes["source"] = (
        "//pubsub.googleapis.com/projects/test-project/"
        "topics/test_unknown_topic"
    )

    with pytest.raises(
        update_operations.UnknownTopicError,
        match=r"^Could not process the message due to unknown Pub/Sub topic: "
        r"projects/test-project/topics/test_unknown_topic\.$"
        "",
    ):
        update_operations.process_pubsub_message(mock_cloud_event)


def test_update_snapshot_data_when_exists(
    mock_snapshot_objects_list: List[models.Snapshots],
):
    """Test the `update_snapshot_data` function.

    Setup and test `update_snapshot_data` when a snapshot with the given sha
    already exists.
    """
    mock_db_connection = Mock()
    mock_db_connection.snapshots_read.return_value = mock_snapshot_objects_list
    update_operations.update_snapshot_data(
        mock_db_connection, MOCK_UPDATE_SNAPSHOT_MSG_DATA
    )
    mock_db_connection.snapshots_update.assert_called_once()


def test_update_snapshot_data_when_not_exists():
    """Test the `update_snapshot_data` function.

    Setup and test `update_snapshot_data` when a snapshot with the given sha
    does not exist.
    """
    mock_db_connection = Mock()
    mock_db_connection.snapshots_read.return_value = []
    update_operations.update_snapshot_data(
        mock_db_connection, MOCK_UPDATE_SNAPSHOT_MSG_DATA
    )
    mock_db_connection.snapshots_create.assert_called_once()


def test_update_snapshot_data_error():
    """Test error handling of the `update_snapshot_data` function."""
    msg_data = b"\n"
    mock_db_connection = Mock()
    with pytest.raises(
        update_operations.UpdateOperationsError,
        match=r"^Unable to parse snapshot data from Pub/Sub message\.$",
    ):
        update_operations.update_snapshot_data(mock_db_connection, msg_data)


def test_update_binhost_data_when_exists(
    mock_build_target_profile_objects_list: List[models.BuildTargetProfiles],
    mock_binhost_objects_list: List[models.Binhosts],
):
    """Test the `update_binhost_data` function when a binhost already exists."""
    mock_db_connection = Mock()
    mock_db_connection.build_target_profiles_create = Mock()
    mock_db_connection.binhosts_update = Mock()
    mock_db_connection.build_target_profiles_filter.return_value = (
        mock_build_target_profile_objects_list
    )
    mock_db_connection.binhosts_filter.return_value = mock_binhost_objects_list

    update_operations.update_binhost_data(
        mock_db_connection, MOCK_UPDATE_SNAPSHOT_MSG_DATA
    )

    # With the test setup, build_target profile and binhost already exist,
    # so only the binhost should be updated.
    mock_db_connection.build_target_profiles_create.assert_not_called()
    mock_db_connection.binhosts_update.assert_called_once()


def test_update_binhost_data_when_not_exists():
    """Test the `update_binhost_data` function when a binhost does not exist."""
    mock_db_connection = Mock()
    mock_db_connection.build_target_profiles_create = Mock()
    mock_db_connection.binhosts_create = Mock()
    mock_db_connection.build_target_profiles_filter.return_value = []
    mock_db_connection.binhosts_filter.return_value = []

    update_operations.update_binhost_data(
        mock_db_connection, MOCK_UPDATE_SNAPSHOT_MSG_DATA
    )
    # With the test setup, both build_target profile and binhost do not exist,
    # so both must be created.
    mock_db_connection.build_target_profiles_create.assert_called_once()
    mock_db_connection.binhosts_create.assert_called_once()


def test_update_binhost_data_error():
    """Test error handling of the `update_binhost_data` function."""
    msg_data = b"\n"
    mock_db_connection = Mock()

    with pytest.raises(
        update_operations.UpdateOperationsError,
        match=r"^Unable to parse binhost data from Pub/Sub message\.$",
    ):
        update_operations.update_binhost_data(mock_db_connection, msg_data)

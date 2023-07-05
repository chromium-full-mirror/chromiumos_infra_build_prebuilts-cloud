# Copyright 2023 The ChromiumOS Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""Module to hold pytest fixtures."""

# Pytest's method of declaring fixtures causes Pylint to complain about
# redefined outer names.
# pylint: disable=redefined-outer-name

# Protected access is needed to mock protected members of classes for tests.
# pylint: disable=protected-access


from typing import Any, Dict, List
from unittest.mock import Mock

# pylint: disable=import-error
from cloudevents.http.event import CloudEvent
import pytest

# pylint: enable=import-error
from lib import config
from lib import db_connector
from lib import models


@pytest.fixture
def mock_snapshot_object() -> models.Snapshots:
    """Fixture to return a mock snapshot object."""

    return models.Snapshots(
        snapshot_sha="", snapshot_num=1, external=True, buildbucket_id=1
    )


@pytest.fixture
def mock_snapshot_objects_list(
    mock_snapshot_object: models.Snapshots,
) -> List[models.Snapshots]:
    """Fixture to return a list of mock snapshot objects."""
    return [mock_snapshot_object]


def setup_mock_db_connection(
    session_attrs: Dict[str, Any],
) -> db_connector.LookupServiceDBConnection:
    """Generic method to setup a mock db connection.

    Return values for the sqlalchemy session are configured based on
    session_attrs.

    Args:
        session_attrs: dictionary containing attributes to be set to the mock
            sqlalchemy session.

    Returns:
        A mock db connection.
    """
    # Mock the _get_engine menthod of LookupServiceDBConnection.
    db_connector.LookupServiceDBConnection._get_engine = Mock()

    lookup_service_db_connection = db_connector.LookupServiceDBConnection(
        "", "", 0, "", ""
    )

    # Mock the _session attribute to have mock db responses from sqlalchemy.
    lookup_service_db_connection._session = Mock(**session_attrs)

    return lookup_service_db_connection


@pytest.fixture
def mock_db_connection() -> db_connector.LookupServiceDBConnection:
    """Fixture to mock a generic db connection to the `lookup_service` DB."""
    return setup_mock_db_connection({})


@pytest.fixture
def mock_snapshots_db_connection(
    mock_snapshot_object: models.Snapshots,
) -> db_connector.LookupServiceDBConnection:
    """Fixture to mock a db connection configured for the snapshot table.

    The sqlalchemy session is configured to mock responses from the snapshots
    table.
    """
    attrs = {
        "query.return_value.get.return_value": mock_snapshot_object,
        "query.return_value.filter.return_value.all.return_value": [
            mock_snapshot_object
        ],
        (
            "query.return_value.filter.return_value.limit.return_value.all."
            "return_value"
        ): [mock_snapshot_object],
    }

    return setup_mock_db_connection(attrs)


@pytest.fixture
def mock_build_target_profile_object() -> models.BuildTargetProfiles:
    """Fixture to return a mock build target profile object."""
    return models.BuildTargetProfiles(
        build_target_profile_id=1,
        build_target="test_build_target",
        profile="test_profile",
    )


@pytest.fixture
def mock_build_target_profile_objects_list(
    mock_build_target_profile_object: models.BuildTargetProfiles,
) -> List[models.BuildTargetProfiles]:
    """Fixture to return a list of mock build_target_profile objects."""
    return [mock_build_target_profile_object]


@pytest.fixture
def mock_build_target_profiles_db_connection(
    mock_build_target_profile_object: models.BuildTargetProfiles,
) -> db_connector.LookupServiceDBConnection:
    """Fixture to mock a db connection configured for build target profiles.

    The sqlalchemy session is configured to mock responses from the build target
    profiles table.
    """
    attrs = {
        "query.return_value.get.return_value": (
            mock_build_target_profile_object
        ),
        "query.return_value.filter.return_value.all.return_value": [
            mock_build_target_profile_object
        ],
        (
            "query.return_value.filter.return_value.limit.return_value.all."
            "return_value"
        ): [mock_build_target_profile_object],
    }

    return setup_mock_db_connection(attrs)


@pytest.fixture
def mock_binhost_object() -> models.Binhosts:
    """Fixture to return a mock binhost object."""
    return models.Binhosts(
        binhost_id=1,
        build_target_profile_id=2,
        snapshot_sha="sha1",
        gs_bucket_name="test_bucket",
        gs_uri="test_uri",
        buildbucket_id=3,
        complete=True,
        private=True,
    )


@pytest.fixture
def mock_query_binhosts_object() -> models.Binhosts:
    """Fixture to return a mock binhost object for `query_binhosts`.

    Return a mock binhost object that would be returned by the
    `db_connector.LookupServiceDBConnection.query_binhosts` method. It contains
    a subset of the columns present in the `binhosts` table.
    """
    return models.Binhosts(
        binhost_id=1, gs_uri="test_uri", created_at=1690272554.842769
    )


@pytest.fixture
def mock_binhost_objects_list(
    mock_binhost_object: models.Binhosts,
) -> List[models.Binhosts]:
    """Fixture to return a list of mock binhost objects."""
    return [mock_binhost_object]


@pytest.fixture
def mock_binhosts_db_connection(
    mock_binhost_object: models.Binhosts,
) -> db_connector.LookupServiceDBConnection:
    """Fixture to mock a db connection configured for the binhosts table.

    The sqlalchemy session is configured to mock responses from the binhosts
    table.
    """
    attrs = {
        "query.return_value.get.return_value": mock_binhost_object,
        "query.return_value.filter.return_value.all.return_value": [
            mock_binhost_object
        ],
        (
            "query.return_value.filter.return_value.limit.return_value.all."
            "return_value"
        ): [mock_binhost_object],
    }

    return setup_mock_db_connection(attrs)


@pytest.fixture
def mock_config_reader() -> config.ConfigReader:
    """Fixture to mock the config reader of the config module.

    Mock the `_defaults` method of the config reader to return mocked
    configuration values.

    Returns:
        A mock config reader object.
    """
    config.ConfigReader._defaults = Mock(
        return_value={
            "lookup_service_db": {
                "database": "test_db",
                "host": "test_host",
                "port": "test_port",
                "username": "test_username",
                "password": "test_password",
            },
            "topics": {
                "update_snapshot_data": "projects/test-project/topics/"
                "test_topic_update_snapshot_data",
                "update_binhost_data": "projects/test-project/topics/"
                "test_topic_update_binhost_data",
            },
        }
    )
    return config.ConfigReader()


@pytest.fixture
def mock_cloud_event() -> CloudEvent:
    """Fixture to return a mock event for cloud functions."""

    # The data in the below Pub/Sub message decodes to:
    # {'snapshot_sha': 'test_sha', 'snapshot_num': 1, 'external': True,
    # 'buildbucket_id': 2}
    return CloudEvent(
        {
            "specversion": "1.0",
            "id": "test_id",
            "source": "//pubsub.googleapis.com/projects/test-project/"
            "topics/test_topic",
            "type": "google.cloud.pubsub.topic.v1.messagePublished",
            "datacontenttype": "application/json",
            "time": "2023-05-09T10:30:56.109Z",
        },
        {
            "message": {
                "attributes": {
                    "googclient_schemaencoding": "BINARY",
                    "googclient_schemarevisionid": "38bc13a5",
                },
                "data": "Cgh0ZXN0X3NoYRABGAEgAg==",
                "messageId": "7636448340173022",
                "message_id": "7636448340173022",
                "publishTime": "2023-05-09T10:30:56.109Z",
                "publish_time": "2023-05-09T10:30:56.109Z",
            },
            "subscription": "projects/test_project/subscriptions/"
            "eventarc-test",
        },
    )

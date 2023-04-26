# Copyright 2023 The ChromiumOS Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""Unit tests for db_connector."""

from unittest.mock import Mock

import pytest
from sqlalchemy.exc import DBAPIError
from sqlalchemy.exc import NoResultFound

from lib import models
from lib.db_connector import DBError
from lib.db_connector import LookupServiceDBConnection


def test_snapshots_create(
    mock_snapshots_db_connection: LookupServiceDBConnection,
):
    """Test the create snapshot method."""
    # Positional args for `snapshots_create`.
    snapshot_args = ("sha1", 1, False, 2)
    created_snapshot = mock_snapshots_db_connection.snapshots_create(
        *snapshot_args
    )

    mock_snapshots_db_connection._session.add.assert_called_once()
    mock_snapshots_db_connection._session.commit.assert_called_once()
    assert type(created_snapshot) == models.Snapshots
    assert (
        created_snapshot.snapshot_sha,
        created_snapshot.snapshot_num,
        created_snapshot.external,
        created_snapshot.buildbucket_id,
    ) == snapshot_args


def test_snapshots_create_error(
    mock_snapshots_db_connection: LookupServiceDBConnection,
):
    """Test error handling of the create snapshot method."""
    # Forcing an error from sqlalchemy commit.
    mock_snapshots_db_connection._session.commit = Mock(
        side_effect=DBAPIError("statement", None, "db error")
    )

    with pytest.raises(DBError, match=r"^Unable to create snapshot record\.$"):
        mock_snapshots_db_connection.snapshots_create("sha1", 1, False, 1)


def test_snapshots_read(
    mock_snapshots_db_connection: LookupServiceDBConnection,
    mock_snapshot_object: models.Snapshots,
):
    """Test the read snapshot method."""
    assert (
        mock_snapshots_db_connection.snapshots_read("sha1")
        == mock_snapshot_object
    )


def test_snapshots_read_error(
    mock_snapshots_db_connection: LookupServiceDBConnection,
):
    """Test error handling of the read snapshot method."""
    # Return None from sqlalchemy get query.
    mock_snapshots_db_connection._session.query.return_value.get.return_value = (
        None
    )

    with pytest.raises(NoResultFound, match=r"^No snapshot record found\.$"):
        mock_snapshots_db_connection.snapshots_read("sha1")


def test_snapshots_filter(
    mock_snapshots_db_connection: LookupServiceDBConnection,
    mock_snapshot_object: models.Snapshots,
):
    """Test the filter snapshot method."""
    assert mock_snapshots_db_connection.snapshots_filter("") == [
        mock_snapshot_object
    ]


def test_snapshots_update(
    mock_snapshots_db_connection: LookupServiceDBConnection,
):
    """Test the update snapshot method."""
    # Assert that the updates have been commited through sqlalchemy.
    mock_snapshots_db_connection.snapshots_update("sha1", 1)
    mock_snapshots_db_connection._session.commit.assert_called_once()


def test_snapshots_update_error(
    mock_snapshots_db_connection: LookupServiceDBConnection,
):
    """Test error handling of the update snapshot method."""
    # Assert DBError is raised when there's no data provided to update the
    # snapshot.
    with pytest.raises(
        DBError, match=r"^No data to update the snapshot record\.$"
    ):
        mock_snapshots_db_connection.snapshots_update("sha1")

    # Assert NoResultFound is raised when no snapshot record is found with
    # the given snapshot_sha.
    mock_snapshots_db_connection._session.query.return_value.get = Mock(
        return_value=None
    )
    with pytest.raises(
        NoResultFound,
        match=r"^No snapshot record found\.$",
    ):
        mock_snapshots_db_connection.snapshots_update("sha1", 1)


def test_snapshots_delete(
    mock_snapshots_db_connection: LookupServiceDBConnection,
):
    """Test the delete snapshots method."""
    # Assert that the delete operation calls have been made through sqlalchemy.
    mock_snapshots_db_connection.snapshots_delete("sha1")
    mock_snapshots_db_connection._session.delete.assert_called_once()
    mock_snapshots_db_connection._session.commit.assert_called_once()


def test_build_target_profiles_create(
    mock_build_target_profiles_db_connection: LookupServiceDBConnection,
):
    """Test the create build target profiles method."""
    # Positional args for `build_target_profiles_create`.
    build_target_profile_args = ("test_build_target", "test_profile")
    created_build_target_profile = (
        mock_build_target_profiles_db_connection.build_target_profiles_create(
            *build_target_profile_args
        )
    )

    mock_build_target_profiles_db_connection._session.add.assert_called_once()
    mock_build_target_profiles_db_connection._session.commit.assert_called_once()
    assert type(created_build_target_profile) == models.BuildTargetProfiles
    assert (
        created_build_target_profile.build_target,
        created_build_target_profile.profile,
    ) == build_target_profile_args


def test_build_target_profiles_create_error(
    mock_build_target_profiles_db_connection: LookupServiceDBConnection,
):
    """Test error handling of the create build target profiles method."""

    # Forcing an error from sqlalchemy commit.
    mock_build_target_profiles_db_connection._session.commit = Mock(
        side_effect=DBAPIError("statement", None, "db error")
    )

    with pytest.raises(
        DBError,
        match=r"^Unable to create build target profile record\.$",
    ):
        mock_build_target_profiles_db_connection.build_target_profiles_create(
            "test", "test"
        )


def test_build_target_profiles_read(
    mock_build_target_profiles_db_connection: LookupServiceDBConnection,
    mock_build_target_profiles_object: models.BuildTargetProfiles,
):
    """Test the read build target profiles method."""

    assert (
        mock_build_target_profiles_db_connection.build_target_profiles_read(1)
        == mock_build_target_profiles_object
    )


def test_build_target_profiles_read_error(
    mock_build_target_profiles_db_connection: LookupServiceDBConnection,
):
    """Test error handling of the read build target profiles method."""

    # Return None from sqlalchemy get query.
    mock_build_target_profiles_db_connection._session.query.return_value.get.return_value = (
        None
    )

    with pytest.raises(
        NoResultFound,
        match=r"^No build target profile record found\.$",
    ):
        mock_build_target_profiles_db_connection.build_target_profiles_read(
            "sha1"
        )

    # Raise DBAPIError from sqlalchemy get query.
    mock_build_target_profiles_db_connection._session.query.return_value.get = (
        Mock(side_effect=DBAPIError("statement", None, "db error"))
    )

    with pytest.raises(
        DBError,
        match=(
            r"^Error when executing the read operation for build target"
            r" profiles\.$"
        ),
    ):
        mock_build_target_profiles_db_connection.build_target_profiles_read(
            "sha1"
        )


def test_build_target_profiles_filter(
    mock_build_target_profiles_db_connection: LookupServiceDBConnection,
    mock_build_target_profiles_object: models.BuildTargetProfiles,
):
    """Test the filter build target profiles method."""

    assert (
        mock_build_target_profiles_db_connection.build_target_profiles_filter(
            ""
        )
        == [mock_build_target_profiles_object]
    )


def test_build_target_profiles_update(
    mock_build_target_profiles_db_connection: LookupServiceDBConnection,
):
    """Test the update build target profiles method."""
    # Assert that the updates have been commited through sqlalchemy.
    mock_build_target_profiles_db_connection.build_target_profiles_update(
        1, "test"
    )
    mock_build_target_profiles_db_connection._session.commit.assert_called_once()


def test_build_target_profiles_update_error(
    mock_build_target_profiles_db_connection: LookupServiceDBConnection,
):
    """Test error handling of the update build target profiles method."""
    # Assert DBError is raised when there's no data provided to update the
    # build target profile.
    with pytest.raises(
        DBError,
        match=r"^No data to update the build target profile record\.$",
    ):
        mock_build_target_profiles_db_connection.build_target_profiles_update(1)

    # Assert NoResultFound is raised when no build target profile record
    # is found with the given build_target_profile_id.
    mock_build_target_profiles_db_connection._session.query.return_value.get = (
        Mock(return_value=None)
    )
    with pytest.raises(
        NoResultFound,
        match=r"^No build target profile record found\.$",
    ):
        mock_build_target_profiles_db_connection.build_target_profiles_update(
            1, "test"
        )


def test_build_target_profiles_delete(
    mock_build_target_profiles_db_connection: LookupServiceDBConnection,
):
    """Test the delete build target profiles method."""
    # Assert that the delete operation calls have been made through sqlalchemy.
    mock_build_target_profiles_db_connection.build_target_profiles_delete(
        "sha1"
    )
    mock_build_target_profiles_db_connection._session.delete.assert_called_once()
    mock_build_target_profiles_db_connection._session.commit.assert_called_once()


def test_binhosts_create(
    mock_binhosts_db_connection: LookupServiceDBConnection,
):
    """Test the create binhosts method."""
    # Positional args for `binhosts_create`.
    binhost_args = (2, "sha1", "test_bucket", "test_uri", 3, True, True)
    created_binhost = mock_binhosts_db_connection.binhosts_create(*binhost_args)

    mock_binhosts_db_connection._session.add.assert_called_once()
    mock_binhosts_db_connection._session.commit.assert_called_once()
    assert type(created_binhost) == models.Binhosts
    assert (
        created_binhost.build_target_profile_id,
        created_binhost.snapshot_sha,
        created_binhost.gs_bucket_name,
        created_binhost.gs_uri,
        created_binhost.buildbucket_id,
        created_binhost.complete,
        created_binhost.private,
    ) == binhost_args


def test_binhosts_create_error(
    mock_binhosts_db_connection: LookupServiceDBConnection,
):
    """Test error handling of the create binhosts method."""
    # Forcing an error from sqlalchemy commit.
    mock_binhosts_db_connection._session.commit = Mock(
        side_effect=DBAPIError("statement", None, "db error")
    )

    with pytest.raises(DBError, match=r"^Unable to create binhost record\.$"):
        mock_binhosts_db_connection.binhosts_create(
            build_target_profile_id=2,
            snapshot_sha="sha1",
            gs_bucket_name="test_bucket",
            gs_uri="test_uri",
            buildbucket_id=3,
            complete=True,
            private=True,
        )


def test_binhosts_read(
    mock_binhosts_db_connection: LookupServiceDBConnection,
    mock_binhost_object: models.Binhosts,
):
    """Test the read binhosts method."""
    assert mock_binhosts_db_connection.binhosts_read(1) == mock_binhost_object


def test_binhosts_read_error(
    mock_binhosts_db_connection: LookupServiceDBConnection,
):
    """Test error handling of the read binhost method."""
    # Return None from sqlalchemy get query.
    mock_binhosts_db_connection._session.query.return_value.get.return_value = (
        None
    )

    with pytest.raises(NoResultFound, match=r"^No binhost record found\.$"):
        mock_binhosts_db_connection.binhosts_read(1)


def test_binhosts_filter(
    mock_binhosts_db_connection: LookupServiceDBConnection,
    mock_binhost_object: models.Binhosts,
):
    """Test the filter binhosts method."""
    assert mock_binhosts_db_connection.binhosts_filter("binhost_id=1") == [
        mock_binhost_object
    ]


def test_binhosts_update(
    mock_binhosts_db_connection: LookupServiceDBConnection,
):
    """Test the update binhosts method."""
    # Assert that the updates have been commited through sqlalchemy.
    mock_binhosts_db_connection.binhosts_update(1, 2)
    mock_binhosts_db_connection._session.commit.assert_called_once()


def test_binhosts_update_error(
    mock_binhosts_db_connection: LookupServiceDBConnection,
):
    """Test error handling of the update binhosts method."""
    # Assert DBError is raised when there's no data provided to update the
    # binhost.
    with pytest.raises(
        DBError, match=r"^No data to update the binhost record\.$"
    ):
        mock_binhosts_db_connection.binhosts_update(1)

    # Assert NoResultFound is raised when no binhost record is found with the
    # given binhost_id.
    mock_binhosts_db_connection._session.query.return_value.get = Mock(
        return_value=None
    )
    with pytest.raises(
        NoResultFound,
        match=r"^No binhost record found\.$",
    ):
        mock_binhosts_db_connection.binhosts_update(1, 2)


def test_binhosts_delete(
    mock_binhosts_db_connection: LookupServiceDBConnection,
):
    """Test the delete binhosts method."""
    # Assert that the delete operation calls have been made through sqlalchemy.
    mock_binhosts_db_connection.binhosts_delete(1)
    mock_binhosts_db_connection._session.delete.assert_called_once()
    mock_binhosts_db_connection._session.commit.assert_called_once()

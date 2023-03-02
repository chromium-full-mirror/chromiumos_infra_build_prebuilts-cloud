# Copyright 2023 The ChromiumOS Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""Unit tests for db_connector."""

from unittest.mock import Mock

import pytest
from sqlalchemy.exc import DBAPIError
from sqlalchemy.exc import NoResultFound

from lib import db_connector


def test_snapshots_create(mock_snapshots_db_connection):
    """Test the create snapshot method."""
    mock_snapshots_db_connection.snapshots_create("sha1", 1, False, 1)
    mock_snapshots_db_connection._session.add.assert_called_once()
    mock_snapshots_db_connection._session.commit.assert_called_once()


def test_snapshots_create_error(mock_snapshots_db_connection):
    """Test error handling of the create snapshot method."""
    # Forcing an error from sqlalchemy commit.
    mock_snapshots_db_connection._session.commit = Mock(
        side_effect=DBAPIError("statement", None, "db error")
    )

    with pytest.raises(
        db_connector.DBError, match="Unable to create snapshot record."
    ):
        mock_snapshots_db_connection.snapshots_create("sha1", 1, False, 1)


def test_snapshots_read(mock_snapshots_db_connection, mock_snapshot_object):
    """Test the read snapshot method."""
    assert (
        mock_snapshots_db_connection.snapshots_read("sha1")
        == mock_snapshot_object
    )


def test_snapshots_read_error(mock_snapshots_db_connection):
    """Test error handling of the read snapshot method."""
    # Return None from sqlalchemy get query.
    mock_snapshots_db_connection._session.query.return_value.get.return_value = (
        None
    )

    with pytest.raises(NoResultFound, match="No snapshot record found."):
        mock_snapshots_db_connection.snapshots_read("sha1")


def test_snapshots_filter(mock_snapshots_db_connection, mock_snapshot_object):
    """Test the filter snapshot method."""
    assert mock_snapshots_db_connection.snapshots_filter("") == [
        mock_snapshot_object
    ]


def test_snapshots_update(mock_snapshots_db_connection):
    """Test the update snapshot method."""
    # Assert that the updates have been commited through sqlalchemy.
    mock_snapshots_db_connection.snapshots_update("sha1", 1)
    mock_snapshots_db_connection._session.commit.assert_called_once()


def test_snapshots_update_error(mock_snapshots_db_connection):
    """Test error handling of the update snapshot method."""
    # Assert DBError is raised when there's no data provided to update the
    # snapshot.
    with pytest.raises(
        db_connector.DBError, match="No data to update the snapshot record."
    ):
        mock_snapshots_db_connection.snapshots_update("sha1")

    # Assert RecordNotFoundError is raised when no snapshot record is found with
    # the given snapshot_sha.
    mock_snapshots_db_connection._session.query.return_value.get = Mock(
        return_value=None
    )
    with pytest.raises(
        NoResultFound,
        match="No snapshot record found.",
    ):
        mock_snapshots_db_connection.snapshots_update("sha1", 1)


def test_snapshots_delete(mock_snapshots_db_connection):
    """Test the update snapshot method."""
    # Assert that the delete operation calls have been made through sqlalchemy.
    mock_snapshots_db_connection.snapshots_delete("sha1")
    mock_snapshots_db_connection._session.delete.assert_called_once()
    mock_snapshots_db_connection._session.commit.assert_called_once()

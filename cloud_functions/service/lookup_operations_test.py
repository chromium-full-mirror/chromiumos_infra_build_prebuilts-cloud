# Copyright 2023 The ChromiumOS Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""Test the lookup_operations module."""

# Protected access is needed to mock protected members of classes for tests.
# pylint: disable=protected-access


from unittest import mock

from protobuf.chromiumos import prebuilts_cloud_pb2
import pytest

from lib import models
from service import lookup_operations


def test__parse_lookup_binhosts_request(mock_lookup_binhosts_request_b64: str):
    """Test the helper function which parses lookup binhosts requests."""
    mock_request = mock.Mock()
    mock_request.args.get.return_value = mock_lookup_binhosts_request_b64(
        private=True, get_corresponding_binhosts=True
    )

    res = lookup_operations._parse_lookup_binhosts_request(mock_request)
    assert isinstance(res, prebuilts_cloud_pb2.LookupBinhostsRequest)
    # Assert the fields in the request are properly parsed.
    assert res.gs_bucket_name == "test_bucket"
    assert res.snapshot_shas == ["test_sha"]
    assert res.build_target == "test_target"
    assert res.profile == "base"
    assert res.private is True
    assert res.get_corresponding_binhosts is True


def test__parse_lookup_binhosts_request_missing_error():
    """Test error handling when filter parameters are missing."""
    mock_request = mock.Mock()
    mock_request.args.get.return_value = b""

    with pytest.raises(
        lookup_operations.ValidationError,
        match=r"^The request does not contain filter parameters\.$",
    ):
        lookup_operations._parse_lookup_binhosts_request(mock_request)


def test__parse_lookup_binhosts_parsing_error():
    """Test error handling when the filter parameters are invalid."""
    mock_request = mock.Mock()
    mock_request.args.get.return_value = b"$12"

    with pytest.raises(
        lookup_operations.ValidationError,
        match=r"^Error while parsing filter parameters from the request\.$",
    ):
        lookup_operations._parse_lookup_binhosts_request(mock_request)


def test__construct_binhosts_response(
    mock_query_binhosts_object: models.Binhosts,
    mock_lookup_binhosts_response_b64: str,
):
    """Test the function used to construct binhosts response."""
    lookup_binhosts_response = lookup_operations._construct_binhosts_response(
        [mock_query_binhosts_object]
    )

    assert lookup_binhosts_response == mock_lookup_binhosts_response_b64


def test_lookup_binhosts_internal(
    mock_lookup_binhosts_request_b64: str,
    mock_lookup_binhosts_response_b64: str,
    mock_db_connection_lookup_binhosts: mock.Mock,
):
    """Test the lookup_binhosts function for the Googlers case."""
    request = mock.Mock()
    request.args.get.return_value = mock_lookup_binhosts_request_b64(
        private=True, get_corresponding_binhosts=True
    )

    response = lookup_operations.lookup_binhosts(
        request, mock_db_connection_lookup_binhosts
    )
    assert response.status_code == 200
    assert response.data == mock_lookup_binhosts_response_b64


def test_lookup_binhosts_partners(
    mock_lookup_binhosts_request_b64: str,
    mock_lookup_binhosts_response_b64: str,
    mock_db_connection_lookup_binhosts: mock.Mock,
):
    """Test the lookup_binhosts function for the partners case."""
    request = mock.Mock()
    request.args.get.return_value = mock_lookup_binhosts_request_b64(
        private=False, get_corresponding_binhosts=True
    )

    response = lookup_operations.lookup_binhosts(
        request, mock_db_connection_lookup_binhosts
    )
    assert response.status_code == 200
    assert response.data == mock_lookup_binhosts_response_b64


def test_lookup_binhosts_external(
    mock_lookup_binhosts_request_b64: str,
    mock_lookup_binhosts_response_b64: str,
    mock_db_connection_lookup_binhosts: mock.Mock,
):
    """Test the lookup_binhosts function for the external developers case."""
    request = mock.Mock()
    request.args.get.return_value = mock_lookup_binhosts_request_b64(
        private=False, get_corresponding_binhosts=False
    )

    response = lookup_operations.lookup_binhosts(
        request, mock_db_connection_lookup_binhosts
    )
    assert response.status_code == 200
    assert response.data == mock_lookup_binhosts_response_b64


def test_lookup_binhosts_bad_request(
    mock_db_connection_lookup_binhosts: mock.Mock,
):
    """Test the lookup_binhosts function when bad request is sent."""
    request = mock.Mock()
    # Return an invalid base64 value.
    request.args.get.return_value = b"$12"

    response = lookup_operations.lookup_binhosts(
        request, mock_db_connection_lookup_binhosts
    )
    assert response.status_code == 400
    assert (
        response.data == b"Unable to parse filter parameters from the request."
    )


def test_lookup_binhosts_build_target_profile_not_found(
    mock_db_connection_lookup_binhosts: mock.Mock,
    mock_lookup_binhosts_request_b64: str,
    monkeypatch,
):
    """Test lookup_binhosts when build target profile is not found."""
    request = mock.Mock()
    request.args.get.return_value = mock_lookup_binhosts_request_b64(
        private=False, get_corresponding_binhosts=False
    )

    # Mock _lookup_build_target_profile_id to return None.
    mock_lookup_build_target_profile_id = mock.Mock()
    monkeypatch.setattr(
        lookup_operations,
        "_lookup_build_target_profile_id",
        mock_lookup_build_target_profile_id,
    )
    mock_lookup_build_target_profile_id.return_value = None

    response = lookup_operations.lookup_binhosts(
        request, mock_db_connection_lookup_binhosts
    )
    assert response.status_code == 404
    assert response.data == b"No binhosts found with the given parameters."


def test_lookup_binhosts_invalid_request(
    mock_db_connection_lookup_binhosts: mock.Mock,
    mock_lookup_binhosts_request_b64: str,
):
    """Test lookup_binhosts when request is invalid."""
    request = mock.Mock()
    # Don't send any snapshot SHAs.
    request.args.get.return_value = mock_lookup_binhosts_request_b64(
        private=False, get_corresponding_binhosts=False, snapshot_shas=[]
    )

    response = lookup_operations.lookup_binhosts(
        request, mock_db_connection_lookup_binhosts
    )
    assert response.status_code == 400
    assert response.data == b"Invalid request, required parameters not present."


def test_lookup_binhosts_generic_build_target_profile_not_found(
    mock_db_connection_lookup_binhosts: mock.Mock,
    mock_lookup_binhosts_request_b64: str,
    monkeypatch,
):
    """Test lookup_binhosts when generic build target profile is not found."""
    request = mock.Mock()
    request.args.get.return_value = mock_lookup_binhosts_request_b64(
        private=False, get_corresponding_binhosts=False
    )

    # Mock _lookup_build_target_profile_id to return None.
    mock_lookup_build_target_profile_id = mock.Mock()
    monkeypatch.setattr(
        lookup_operations,
        "_lookup_build_target_profile_id",
        mock_lookup_build_target_profile_id,
    )
    mock_lookup_build_target_profile_id.side_effect = [None, None]

    response = lookup_operations.lookup_binhosts(
        request, mock_db_connection_lookup_binhosts
    )
    assert response.status_code == 404
    assert response.data == b"No binhosts found with the given parameters."


def test_lookup_binhosts_binhosts_not_found(
    mock_db_connection_lookup_binhosts: mock.Mock,
    mock_lookup_binhosts_request_b64: str,
):
    """Test lookup_binhosts response when no binhosts are found."""
    request = mock.Mock()
    request.args.get.return_value = mock_lookup_binhosts_request_b64(
        private=True, get_corresponding_binhosts=True
    )

    # Overwrite the fixture return value so that no binhosts are found.
    mock_db_connection_lookup_binhosts.query_binhosts.side_effect = ([], [])

    response = lookup_operations.lookup_binhosts(
        request, mock_db_connection_lookup_binhosts
    )
    assert response.status_code == 404
    assert response.data == b"No binhosts found with the given parameters."

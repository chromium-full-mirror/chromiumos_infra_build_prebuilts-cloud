# Copyright 2023 The ChromiumOS Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""Lookup operations on the `lookup_service` database."""

import base64
import binascii
import decimal
import logging
from typing import List, Optional

# pylint: disable=import-error
import flask
import flask.wrappers
from google.protobuf import message
from google.protobuf import timestamp_pb2
from protobuf.chromiumos import prebuilts_cloud_pb2

# pylint: enable=import-error
from lib import db_connector
from lib import models


class LookupOperationsError(Exception):
    """Base error class for the module."""


class ValidationError(LookupOperationsError):
    """Error when validating inputs."""


def _parse_lookup_binhosts_request(
    request: flask.wrappers.Request,
) -> prebuilts_cloud_pb2.LookupBinhostsRequest:
    """Parse flask request and return a LookupBinhostsRequest object.

    Args:
        request: Flask request object containing parameters to lookup binhosts.

    Returns:
        An instance of `prebuilts_cloud_pb2.LookupBinhostsRequest`.

    Raises:
        binascii.Error: When the `filter` param cannot be base64 decoded.
        google.protobuf.message.DecodeError: When the protobuf message cannot be
            parsed.
        TypeError: When the `filter` param is not present in the request.
    """
    filter_params = request.args.get("filter")
    if not filter_params:
        raise ValidationError("The request does not contain filter parameters.")

    try:
        filter_params_decoded = base64.urlsafe_b64decode(filter_params)
        lookup_service_request = prebuilts_cloud_pb2.LookupBinhostsRequest()
        lookup_service_request.ParseFromString(filter_params_decoded)
    except (binascii.Error, message.DecodeError, TypeError) as err:
        logging.error(err)
        raise ValidationError(
            "Error while parsing filter parameters from the request."
        ) from err

    return lookup_service_request


def _construct_binhosts_response(binhosts: List[models.Binhosts]) -> bytes:
    """Construct a base64 encoded response with binhosts data.

    Args:
        binhosts: A list of binhost objects, each containing the `binhost_id`,
            `gs_uri` and `created_at` columns.

    Returns:
        A `prebuilts_cloud_pb2.LookupBinhostsResponse` object encoded with
        base64, in bytes.
    """
    response = prebuilts_cloud_pb2.LookupBinhostsResponse()
    for binhost in binhosts:
        created_at = timestamp_pb2.Timestamp()
        # Add a check for created_at, since some older records in the staging DB
        # don't have this field populated.
        if binhost.created_at:
            # postgres stores timestamps with microsecond precision, so creating
            # a `timestamp_pb2.Timestamp` object from microseconds.
            created_at.FromMicroseconds(
                int(decimal.Decimal(binhost.created_at) * decimal.Decimal(1e6))
            )

        response.binhosts.append(
            prebuilts_cloud_pb2.LookupBinhostsResponse.Binhost(
                binhost_id=binhost.binhost_id,
                gs_uri=binhost.gs_uri,
                created_at=created_at,
            )
        )

    # Encode the protobuf message with base64.
    return base64.urlsafe_b64encode(response.SerializeToString())


def _lookup_build_target_profile_id(
    db_connection: db_connector.LookupServiceDBConnection,
    build_target: str,
    profile: str,
) -> Optional[int]:
    """Lookup build target profile id.

    Args:
        db_connection: Connection object to the `lookup_service` database.
        build_target: The name of the build target.
        profile: The name of the profile for the build target.

    Returns:
        The id of the build target profile, if found.
    """
    build_target_profiles = db_connection.build_target_profiles_filter(
        f"build_target='{build_target}' AND profile='{profile}'",
        limit=1,
    )
    if not build_target_profiles:
        return None
    return build_target_profiles[0].build_target_profile_id


def lookup_binhosts(
    request: flask.wrappers.Request,
    lookup_service_db_connection: db_connector.LookupServiceDBConnection,
) -> flask.Response:
    """Lookup binhosts and return their storage locations.

    Args:
        request: Flask request object containing filter parameters to lookup
            binhosts.
        lookup_service_db_connection: Connection object to the `lookup_service`
            database.

    Returns:
        A flask response object containing a
        `prebuilts_cloud_pb2.LookupBinhostsResponse` object encoded with base64,
        in bytes.
    """
    try:
        lookup_service_request = _parse_lookup_binhosts_request(request)
    except ValidationError:
        return flask.Response(
            "Unable to parse filter parameters from the request.", status=400
        )
    logging.info("lookup_service_request: \n%s", lookup_service_request)

    if not lookup_service_request.snapshot_shas:
        error_msg = "Invalid request, required parameters not present."
        logging.info(error_msg)
        return flask.Response(error_msg, status=400)

    # Get the build_target_profile ids based on the filter parameters.
    build_target_profile_id = _lookup_build_target_profile_id(
        lookup_service_db_connection,
        lookup_service_request.build_target,
        lookup_service_request.profile,
    )

    if build_target_profile_id is None:
        error_msg = "Build target profile not found."
        logging.info(error_msg)

    generic_build_target_profile_id = _lookup_build_target_profile_id(
        lookup_service_db_connection,
        lookup_service_request.generic_build_target,
        lookup_service_request.generic_profile,
    )

    if generic_build_target_profile_id is None:
        error_msg = "Generic build target profile not found."
        logging.info(error_msg)

    binhosts = []
    private = lookup_service_request.private

    # Get additional snapshot SHAs.
    snapshot_shas = lookup_service_db_connection.get_additional_snapshot_shas(
        lookup_service_request.snapshot_shas, private, count=50
    )

    if not snapshot_shas:
        error_msg = "Snapshot SHAs not found."
        logging.info(error_msg)
        return flask.Response(error_msg, status=404)

    # Fetch the binhosts from the DB.
    logging.info("Now attempting to fetch binhosts...")

    # Internal case.
    if private:
        # Only local builds will require corresponding binhosts.
        if lookup_service_request.get_corresponding_binhosts:
            external_shas = (
                lookup_service_db_connection.get_corresponding_snapshot_shas(
                    snapshot_shas,
                    private=True,
                )
            )
            logging.info(
                "Fetched corresponding external SHAs: %s", external_shas
            )
            if generic_build_target_profile_id and external_shas:
                binhosts.extend(
                    lookup_service_db_connection.query_binhosts(
                        lookup_service_request.gs_bucket_name,
                        external_shas,
                        generic_build_target_profile_id,
                        private=False,
                    )
                )
        if build_target_profile_id:
            binhosts.extend(
                lookup_service_db_connection.query_binhosts(
                    lookup_service_request.gs_bucket_name,
                    snapshot_shas,
                    build_target_profile_id,
                    private=True,
                )
            )
    # Partners case.
    elif not private and lookup_service_request.get_corresponding_binhosts:
        internal_shas = (
            lookup_service_db_connection.get_corresponding_snapshot_shas(
                snapshot_shas,
                private=False,
            )
        )
        logging.info("Fetched corresponding internal SHAs: %s", internal_shas)
        if build_target_profile_id and internal_shas:
            binhosts.extend(
                lookup_service_db_connection.query_binhosts(
                    lookup_service_request.gs_bucket_name,
                    internal_shas,
                    build_target_profile_id,
                    private=True,
                )
            )
        if generic_build_target_profile_id:
            binhosts.extend(
                lookup_service_db_connection.query_binhosts(
                    lookup_service_request.gs_bucket_name,
                    snapshot_shas,
                    generic_build_target_profile_id,
                    private=False,
                )
            )
    # External case.
    else:
        if build_target_profile_id:
            binhosts.extend(
                lookup_service_db_connection.query_binhosts(
                    lookup_service_request.gs_bucket_name,
                    snapshot_shas,
                    build_target_profile_id,
                    private=False,
                )
            )

    if not binhosts:
        error_msg = "No binhosts found with the given parameters."
        logging.info(error_msg)
        return flask.Response(error_msg, status=404)

    binhosts_to_return = binhosts[:5]  # Limit the number of binhosts returned.

    binhost_ids = [x.binhost_id for x in binhosts_to_return]
    # Update the `last_accessed` column with the current timestamp.
    lookup_service_db_connection.update_binhosts_last_accessed(binhost_ids)

    logging.info("Found binhosts: %s", binhosts_to_return)
    return flask.Response(
        response=_construct_binhosts_response(binhosts_to_return), status=200
    )

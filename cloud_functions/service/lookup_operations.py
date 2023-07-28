# Copyright 2023 The ChromiumOS Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""Lookup operations on the `lookup_service` database."""

import base64
import binascii
import decimal
import logging
from typing import List

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
        # postgres stores timestamps with microsecond precision, so creating a
        # `timestamp_pb2.Timestamp` object from microseconds.
        created_at = timestamp_pb2.Timestamp()
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

    # Get the build_target_profile id based on the filter parameters.
    build_target_profiles = (
        lookup_service_db_connection.build_target_profiles_filter(
            f"build_target='{lookup_service_request.build_target}' AND "
            f"profile='{lookup_service_request.profile}'",
            limit=1,
        )
    )
    if not build_target_profiles:
        return flask.Response("Build target profile not found", status=404)
    build_target_profile_id = build_target_profiles[0].build_target_profile_id

    # Fetch binhosts from the DB.
    binhosts = lookup_service_db_connection.query_binhosts(
        lookup_service_request.gs_bucket_name,
        lookup_service_request.snapshot_shas,
        build_target_profile_id,
        lookup_service_request.private,
    )

    if not binhosts:
        return flask.Response(
            "No binhosts found with the given parameters", status=404
        )

    binhost_ids = [x.binhost_id for x in binhosts]
    # Update the `last_accessed` column with the current timestamp.
    lookup_service_db_connection.update_binhosts_last_accessed(binhost_ids)

    return flask.Response(
        response=_construct_binhosts_response(binhosts), status=200
    )

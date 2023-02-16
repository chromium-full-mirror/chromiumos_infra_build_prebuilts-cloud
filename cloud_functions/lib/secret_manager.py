# Copyright 2023 The ChromiumOS Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""Functionality for getting secrets using the secretmanager GCP client."""

import os
from typing import Optional

from google.cloud import secretmanager
import google_crc32c

from lib import constants


class Error(Exception):
    """Base error class for the module."""


class DataCorruptionError(Error):
    """Error when data corruption is detected."""


class LookupServiceDbSecrets:
    """Secrets for the database in differentß environments."""

    def __init__(self) -> None:
        """Init method."""
        self.staging = True if os.environ.get("STAGING") else False

    @property
    def database_name(self) -> str:
        """Gets the database name."""
        secret = "prebuilts-staging-db" if self.staging else "prebuilts-db"
        return _get_secret(secret)

    @property
    def user(self) -> str:
        """Gets the database user."""
        secret = "prebuilts-staging-user" if self.staging else "prebuilts-user"
        return _get_secret(secret)

    @property
    def password(self) -> str:
        """Gets the database password."""
        secret = "prebuilts-staging-pw" if self.staging else "prebuilts-pw"
        return _get_secret(secret)


def _get_secret(secret: str, version: str = "latest") -> str:
    """Gets a secret from the Secret Manager.

    Args:
        secret: Name of secret to retrieve payload for.
        version: Specifies a version for the secret.

    Returns:
        Payload for the given secret.
    """
    client = secretmanager.SecretManagerServiceClient()
    name = (
        f"projects/{constants.PROJECT_ID}/secrets/{secret}/versions/{version}"
    )
    response = client.access_secret_version(request={"name": name})

    crc32c = google_crc32c.Checksum()
    crc32c.update(response.payload.data)
    if response.payload.data_crc32c != int(crc32c.hexdigest(), 16):
        raise DataCorruptionError(
            "Data corruption detected accessing secret: %s", secret
        )

    return response.payload.data.decode("UTF-8")

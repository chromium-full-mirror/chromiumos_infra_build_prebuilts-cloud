# Copyright 2023 The ChromiumOS Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""Reader for commonly used configuration parameters."""

import copy
import os
from typing import Any, Dict

from lib import secret_manager


class ConfigReader:
    """Reader for configuration parameters.

    A common place to access configuration parameters coming from different
    sources like environment variables, secret manager, etc. Additional logic
    and formatting can be done here before they are returned.
    """

    def __init__(self) -> None:
        """Init method."""
        self._CONFIG = {}

    def _defaults(self) -> Dict[str, Any]:
        """Return default configuration parameters.

        Returns:
            A dictionary containing configuration parameters.
        """
        # secret manager client.
        secrets = secret_manager.LookupServiceDbSecrets()
        return {
            "lookup_service_db": {
                "database": secrets.database_name,
                "host": os.environ.get("PREBUILTS_SQL_INSTANCE_HOST"),
                "port": os.environ.get("PREBUILTS_SQL_INSTANCE_PORT"),
                "username": secrets.user,
                "password": secrets.password,
            },
            "topics": {
                "update_snapshot_data": os.environ.get(
                    "TOPIC_NAME_UPDATE_SNAPSHOT_DATA"
                ),
                "update_binhost_data": os.environ.get(
                    "TOPIC_NAME_UPDATE_BINHOST_DATA"
                ),
            },
        }

    def initialize_defaults(self) -> None:
        """Initialize default configuration parameters."""
        self._CONFIG.update(self._defaults())

    def get(self, key: str) -> Dict[str, Any]:
        """Get configuration values based on the key.

        Args:
            key: Name of the configuration parameters to be retrieved.

        Returns:
            A dictionary containing the subset of configuration parameters based
                on the key.

        Raises:
            KeyNotFoundError: When the key is not present in the Config Reader.
        """
        return copy.deepcopy(self._CONFIG[key])


# This is a singleton object that can be imported and used.
# The default values are initialized in main.py.
READER = ConfigReader()

# Copyright 2023 The ChromiumOS Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""Functionality for performing database operations."""

import sqlalchemy
from sqlalchemy.orm import sessionmaker


class DBError(Exception):
    """Base error class for the module."""


class LookupServiceDBConnection:
    """Connection to the lookup service database.

    Attributes:
        database: Name of the lookup service database.
        host: Host name of the cloud sql instance.
        port: Port for the cloud sql instance.
        username: Username for the cloud sql instance user account.
        password: Password for the cloud sql instance user account.
    """

    def __init__(
        self,
        database: str,
        host: str,
        port: int,
        username: str,
        password: str,
    ) -> None:
        """Init method."""

        self.database = database
        self.host = host
        self.port = port
        self.username = username
        self.password = password

        self._engine = self._get_engine()
        self._session = sessionmaker(bind=self._engine)()

    def _get_engine(self) -> sqlalchemy.engine.base.Engine:
        """Get an sqlalchemy engine for the database.

        Returns:
            An sqlalchemy engine for the database.
        """

        engine = sqlalchemy.create_engine(
            sqlalchemy.engine.url.URL.create(
                drivername="postgresql+pg8000",
                database=self.database,
                host=self.host,
                port=self.port,
                username=self.username,
                password=self.password,
            )
        )

        return engine

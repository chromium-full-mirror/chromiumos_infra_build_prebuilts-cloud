# Copyright 2023 The ChromiumOS Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""Functionality for performing database operations."""


from typing import List, Optional

import sqlalchemy
from sqlalchemy.exc import DBAPIError
from sqlalchemy.exc import NoResultFound
import sqlalchemy.orm

from lib.models import Snapshots


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
        self._session = self._get_session()

    def _get_engine(self) -> sqlalchemy.engine.base.Engine:
        """Get a sqlalchemy engine for the database.

        Returns:
            A sqlalchemy engine for the database.
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

    def _get_session(self) -> sqlalchemy.orm.session.Session:
        """Create a sqlalchemy session for the database.

        Returns:
            A sqlalchemy session for the database.
        """
        return sqlalchemy.orm.sessionmaker(bind=self._engine)()

    def snapshots_create(
        self,
        snapshot_sha: str,
        snapshot_num: int,
        external: bool,
        buildbucket_id: int,
    ) -> None:
        """Insert a snapshot record.

        Args:
            snapshot_sha: Unique sha of the snapshot.
            snapshot_num: Snapshot number.
            external: Boolean to denote if the snapshot is external.
            buildbucket_id: Id of the annealing build that created the snapshot.

        Raises:
            DBError: When the insert operation fails.
        """
        new_snapshot = Snapshots(
            snapshot_sha=snapshot_sha,
            snapshot_num=snapshot_num,
            external=external,
            buildbucket_id=buildbucket_id,
        )
        self._session.add(new_snapshot)
        try:
            self._session.commit()
        except DBAPIError as sql_error:
            raise DBError("Unable to create snapshot record.") from sql_error

    def snapshots_read(
        self, snapshot_sha: str, required: bool = True
    ) -> Optional[Snapshots]:
        """Read from the snapshots table based on snapshot_sha.

        Args:
            snapshot_sha: Unique sha of the snapshot to read.
            required: Bool to indicate if it is compulsory to return a snapshot.

        Returns:
            A Snapshot object if present, returns None otherwise.

        Raises:
            DBError: When the read operation fails.
            NoResultFound: When required=True and no snapshot is found.
        """
        try:
            result = self._session.query(Snapshots).get(snapshot_sha)
            if required and result is None:
                raise NoResultFound("No snapshot record found.")
            return result
        except DBAPIError as sql_error:
            raise DBError(
                "Error when executing the read operation."
            ) from sql_error

    def snapshots_filter(self, filter_exp: str) -> List[Snapshots]:
        """Filter and read from the snapshots table.

        Args:
            filter_exp: Textual sql filter expression that would be in a sql
                WHERE clause. e.g. "external=True AND buildbucket_id='123'".

        Returns:
            A list of Snapshot objects based on the filter.

        Raises:
            DBError: When the sql filter query fails.
        """
        try:
            result = (
                self._session.query(Snapshots)
                .filter(sqlalchemy.text(filter_exp))
                .all()
            )
            return result
        except DBAPIError as sql_error:
            raise DBError(
                "Error when executing the filter query."
            ) from sql_error

    def snapshots_update(
        self,
        snapshot_sha: str,
        snapshot_num: int = None,
        external: bool = None,
        buildbucket_id: int = None,
    ) -> None:
        """Update a snapshot.

        Args:
            snapshot_sha: Unique sha used to find a snapshot to update.
            snapshot_num: If given, new snapshot_number value for the snapshot.
            external: If given, new external value for the snapshot.
            buildbucket_id: If given, new buildbucket_id value for the snapshot.

        Raises:
            DBError: When no data is sent to update the snapshot record or if
            there is a database operation error from sqlalchemy.
        """
        if snapshot_num is None and external is None and buildbucket_id is None:
            raise DBError("No data to update the snapshot record.")

        snapshot_to_update = self.snapshots_read(snapshot_sha)

        if snapshot_num is not None:
            snapshot_to_update.snapshot_num = snapshot_num

        if external is not None:
            snapshot_to_update.external = external

        if buildbucket_id is not None:
            snapshot_to_update.buildbucket_id = buildbucket_id

        try:
            self._session.commit()
        except DBAPIError as sql_error:
            raise DBError(
                "Error when updating the snapshot record."
            ) from sql_error

    def snapshots_delete(
        self,
        snapshot_sha: str,
    ) -> None:
        """Delete a snapshot.

        Args:
            snapshot_sha: Unique sha of the snapshot.

        Raises:
            DBError: when delete operation fails.
        """
        snapshot_to_delete = self.snapshots_read(snapshot_sha)
        try:
            self._session.delete(snapshot_to_delete)
            self._session.commit()
        except DBAPIError as sql_error:
            raise DBError(
                "Error when deleting the snapshot record."
            ) from sql_error

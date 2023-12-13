# Copyright 2023 The ChromiumOS Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""Functionality for performing database operations."""

from typing import Any, List, Optional

# pylint: disable=import-error
import sqlalchemy
import sqlalchemy.exc
import sqlalchemy.orm

# pylint: enable=import-error
from lib import models


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

    def _commit_session(self, error_msg: str) -> None:
        """Commit the current sqlalchemy session to the DB.

        Args:
            error_msg: A descriptive error message when the commit transaction
                fails.

        Raises:
            DBError: When the commit transaction fails.
        """
        try:
            self._session.commit()
        except sqlalchemy.exc.DBAPIError as sql_error:
            raise DBError(error_msg) from sql_error

    def _execute_filter(
        self,
        model: sqlalchemy.orm.decl_api.DeclarativeMeta,
        filter_exp: str,
        limit: Optional[int] = None,
    ) -> List[Any]:
        """Filter and read data from a specific table.

        Generic method to execute a filter on a table. The class of the
        SQLAlchemy ORM model must be passed as a reference.

        Args:
            model: SQLAlchemy model to apply the filter to.
            filter_exp: Textual sql filter expression that would be in a sql
                WHERE clause. e.g. "external=True AND buildbucket_id='123'". The
                fields in the expression must be specific to the table.
            limit: Max number of records to return.

        Returns:
            A list of model objects based on the filter.

        Raises:
            DBError: When the sql filter query fails.
        """
        query = self._session.query(model).filter(sqlalchemy.text(filter_exp))
        if limit:
            query = query.limit(limit)
        try:
            result = query.all()
        except sqlalchemy.exc.DBAPIError as sql_error:
            raise DBError(
                "Error when executing the filter query."
            ) from sql_error
        return result

    def _execute_query(
        self,
        sql_query: sqlalchemy.orm.query.Query,
    ) -> List[Any]:
        """Execute a SQL query.

        Generic method to execute a SQL query.

        Args:
            sql_query: SQL query to be executed.

        Returns:
            A list of SQLAlchemy objects.

        Raises:
            DBError: When the sql query fails.
        """
        try:
            result = sql_query.all()
        except sqlalchemy.exc.DBAPIError as sql_error:
            raise DBError("Error when executing the sql query.") from sql_error
        return result

    def snapshots_create(
        self,
        snapshot_sha: str,
        snapshot_num: int,
        external: bool,
        buildbucket_id: int,
    ) -> models.Snapshots:
        """Insert a snapshot record.

        Args:
            snapshot_sha: Unique sha of the snapshot.
            snapshot_num: Snapshot number.
            external: Boolean to denote if the snapshot is external.
            buildbucket_id: Id of the annealing build that created the snapshot.

        Returns:
            The snapshot object that is created.

        Raises:
            DBError: When the insert operation fails.
        """
        new_snapshot = models.Snapshots(
            snapshot_sha=snapshot_sha,
            snapshot_num=snapshot_num,
            external=external,
            buildbucket_id=buildbucket_id,
        )
        self._session.add(new_snapshot)
        self._commit_session(error_msg="Unable to create snapshot record.")
        return new_snapshot

    def snapshots_read(
        self, snapshot_sha: str, required: bool = True
    ) -> Optional[models.Snapshots]:
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
            result = self._session.query(models.Snapshots).get(snapshot_sha)
            if required and result is None:
                raise sqlalchemy.exc.NoResultFound("No snapshot record found.")
            return result
        except sqlalchemy.exc.DBAPIError as sql_error:
            raise DBError(
                "Error when executing the read operation."
            ) from sql_error

    def snapshots_filter(
        self, filter_exp: str, limit: Optional[int] = None
    ) -> List[models.Snapshots]:
        """Filter and read from the snapshots table.

        Args:
            filter_exp: Textual sql filter expression that would be in a sql
                WHERE clause. e.g. "external=True AND buildbucket_id='123'".
            limit: Max number of records to return.

        Returns:
            A list of Snapshot objects based on the filter.

        Raises:
            DBError: When the sql filter query fails.
        """
        return self._execute_filter(models.Snapshots, filter_exp, limit)

    def snapshots_update(
        self,
        snapshot_sha: str,
        snapshot_num: Optional[int] = None,
        external: Optional[bool] = None,
        buildbucket_id: Optional[int] = None,
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
            NoResultFound: When no snapshot is found.
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

        self._commit_session(
            error_msg="Error when updating the snapshot record."
        )

    def snapshots_delete(
        self,
        snapshot_sha: str,
    ) -> None:
        """Delete a snapshot.

        Args:
            snapshot_sha: Unique sha of the snapshot.

        Raises:
            DBError: when delete operation fails.
            NoResultFound: When no snapshot is found.
        """
        snapshot_to_delete = self.snapshots_read(snapshot_sha)
        self._session.delete(snapshot_to_delete)
        self._commit_session(
            error_msg="Error when deleting the snapshot record."
        )

    def build_target_profiles_create(
        self,
        build_target: str,
        profile: str,
    ) -> models.BuildTargetProfiles:
        """Insert a build target profile record.

        Args:
            build_target: The system Chrome OS is being built for, also known
                as board.
            profile: Name of the profile to use with the build_target.

        Returns:
            The build target profile object that is created.

        Raises:
            DBError: When the insert operation fails.
        """
        new_build_target_profile = models.BuildTargetProfiles(
            build_target=build_target,
            profile=profile,
        )
        self._session.add(new_build_target_profile)
        self._commit_session(
            error_msg="Unable to create build target profile record."
        )
        return new_build_target_profile

    def build_target_profiles_read(
        self, build_target_profile_id: int, required: bool = True
    ) -> Optional[models.Snapshots]:
        """Read from build target profiles based on build_target_profile_id.

        Args:
            build_target_profile_id: Id of the build target profile to read.
            required: Bool to indicate if it is compulsory to return a
                build target profile.

        Returns:
            A build target profile object if present, returns None otherwise.

        Raises:
            DBError: When the read operation fails.
            NoResultFound: When required=True and no build target profile
                is found.
        """
        try:
            result = self._session.query(models.BuildTargetProfiles).get(
                build_target_profile_id
            )

            if required and result is None:
                raise sqlalchemy.exc.NoResultFound(
                    "No build target profile record found."
                )

            return result
        except sqlalchemy.exc.DBAPIError as sql_error:
            raise DBError(
                "Error when executing the read operation for build target"
                " profiles."
            ) from sql_error

    def build_target_profiles_filter(
        self, filter_exp: str, limit: Optional[int] = None
    ) -> List[models.BuildTargetProfiles]:
        """Filter and read from the build_target_profiles table.

        Args:
            filter_exp: Textual sql filter expression that would be in a
                sql WHERE clause. e.g."build_target='brya'".
            limit: Max number of records to return.

        Returns:
            A list of build target profile objects based on the filter.

        Raises:
            DBError: When the sql filter query fails.
        """
        return self._execute_filter(
            models.BuildTargetProfiles, filter_exp, limit
        )

    def build_target_profiles_update(
        self,
        build_target_profile_id: int,
        build_target: Optional[str] = None,
        profile: Optional[str] = None,
    ) -> None:
        """Update a snapshot.

        Args:
            build_target_profile_id: Id of the build target profile to be
                updated.
            build_target: If given, new build target value for the build target
                profile.
            profile: If given, new profile value for the build target profile.

        Raises:
            DBError: When no data is sent to update the build target profile
                record or if there's a database operation error from sqlalchemy.
            NoResultFound: When no build target profile is found.
        """
        if build_target is None and profile is None:
            raise DBError("No data to update the build target profile record.")

        build_target_profile_to_update = self.build_target_profiles_read(
            build_target_profile_id
        )

        if build_target is not None:
            build_target_profile_to_update.build_target = build_target

        if profile is not None:
            build_target_profile_to_update.profile = profile

        self._commit_session(
            error_msg="Error when updating the build target profile record."
        )

    def build_target_profiles_delete(
        self,
        build_target_profile_id: int,
    ) -> None:
        """Delete a build target profile.

        Args:
            build_target_profile_id: Id of the build target profile to delete.

        Raises:
            DBError: When delete operation fails.
            NoResultFound: When no build target profile is found.
        """
        build_target_profile_to_delete = self.build_target_profiles_read(
            build_target_profile_id
        )
        self._session.delete(build_target_profile_to_delete)
        self._commit_session(
            error_msg="Error when deleting the build target profile record."
        )

    def binhosts_create(
        self,
        build_target_profile_id: int,
        snapshot_sha: str,
        gs_bucket_name: str,
        gs_uri: str,
        buildbucket_id: int,
        complete: bool,
        private: bool,
    ) -> models.Binhosts:
        """Insert a binhost record.

        Args:
            build_target_profile_id: Foreign key for the build target profile.
            snapshot_sha: Foreign key for the snapshot associated with the
                binhost.
            gs_bucket_name: Name of the google storage bucket which contains the
                binhost.
            gs_uri: Location of the binhost object in google storage.
            buildbucket_id: Id of the postsubmit builder that created and
                uploaded the binhost.
            complete: Bool to indicate if this binhost contains all the binpkgs
                specified in the packages metadata file.
            private: Bool to indicate if the binhost is private.

        Returns:
            The binhost object that is created.

        Raises:
            DBError: When the insert operation fails.
        """
        new_binhost = models.Binhosts(
            build_target_profile_id=build_target_profile_id,
            snapshot_sha=snapshot_sha,
            gs_bucket_name=gs_bucket_name,
            gs_uri=gs_uri,
            buildbucket_id=buildbucket_id,
            complete=complete,
            private=private,
        )
        self._session.add(new_binhost)
        self._commit_session(error_msg="Unable to create binhost record.")
        return new_binhost

    def binhosts_read(
        self, binhost_id: str, required: bool = True
    ) -> Optional[models.Binhosts]:
        """Read from the binhosts table based on binhost_id.

        Args:
            binhost_id: Id of the binhost to read.
            required: Bool to indicate if it is compulsory to return a binhost.

        Returns:
            A binhost object if present, returns None otherwise.

        Raises:
            DBError: When the read operation fails.
            NoResultFound: When required=True and no binhost is found.
        """
        try:
            result = self._session.query(models.Binhosts).get(binhost_id)
        except sqlalchemy.exc.DBAPIError as sql_error:
            raise DBError(
                "Error when executing the read operation for binhosts."
            ) from sql_error

        if required and result is None:
            raise sqlalchemy.exc.NoResultFound("No binhost record found.")
        return result

    def binhosts_filter(
        self, filter_exp: str, limit: Optional[int] = None
    ) -> List[models.Binhosts]:
        """Filter and read from the binhosts table.

        Args:
            filter_exp: Textual sql filter expression that would be in a
                sql WHERE clause. e.g."private=True AND snapshot_sha='123'".
            limit: Max number of records to return.

        Returns:
            A list of binhost objects based on the filter.

        Raises:
            DBError: When the sql filter query fails.
        """
        return self._execute_filter(models.Binhosts, filter_exp, limit)

    def binhosts_update(
        self,
        binhost_id: int,
        build_target_profile_id: Optional[int] = None,
        snapshot_sha: Optional[str] = None,
        gs_bucket_name: Optional[str] = None,
        gs_uri: Optional[str] = None,
        buildbucket_id: Optional[int] = None,
        complete: Optional[bool] = None,
        private: Optional[bool] = None,
    ) -> None:
        """Update a binhost.

        Args:
            binhost_id: Id of the binhost to be updated.
            build_target_profile_id: If given, new build_target_profile_id value
                for the binhost.
            snapshot_sha: If given, new snapshot_sha value for the binhost.
            gs_bucket_name: If given, new gs_bucket_name value for the binhost.
            gs_uri: If given, new gs_uri value for the binhost.
            buildbucket_id: If given, new buildbucket_id value for the binhost.
            complete: If given, new complete value for the binhost.
            private: If given, new private value for the binhost.

        Raises:
            DBError: When no data is sent to update the binhost record or if
                there is a database operation error from sqlalchemy.
            NoResultFound: When no binhost is found.
        """

        # Construct dict for easy iteration when applying updates.
        update_attrs = {
            "build_target_profile_id": build_target_profile_id,
            "snapshot_sha": snapshot_sha,
            "gs_bucket_name": gs_bucket_name,
            "gs_uri": gs_uri,
            "buildbucket_id": buildbucket_id,
            "complete": complete,
            "private": private,
        }

        # Raise an error if there is no new data to update the binhost.
        if all(val is None for val in update_attrs.values()):
            raise DBError("No data to update the binhost record.")

        binhost_to_update = self.binhosts_read(binhost_id)

        # Assign new values to the binhost_to_update object.
        for key, val in update_attrs.items():
            if val is not None:
                setattr(binhost_to_update, key, val)

        self._commit_session(
            error_msg="Error when updating the binhost record."
        )

    def binhosts_delete(
        self,
        binhost_id: int,
    ) -> None:
        """Delete a binhost.

        Args:
            binhost_id: Id of the binhost to delete.

        Raises:
            DBError: when delete operation fails.
            NoResultFound: When no binhost is found.
        """

        binhost_to_delete = self.binhosts_read(binhost_id)
        self._session.delete(binhost_to_delete)
        self._commit_session(
            error_msg="Error when deleting the binhost record."
        )

    def get_corresponding_snapshot_shas(
        self, snapshot_shas: List[str], private: bool
    ) -> List[Optional[str]]:
        """Query for the corresponding public or private snapshot SHAs.

        If the provided SHAs are public, return the corresponding private SHAs.
        If the provided SHAs are private, return the corresponding public SHAs.

        Args:
            snapshot_shas: A list of snapshot SHAs.
            private: True if the provided list of SHAs are private.

        Returns:
            A list of snapshot SHAs, if found.

        Raises:
            DBError: When the sql query fails.
        """
        # Construct string of snapshot SHAs, to be used in the SQL query.
        snapshot_shas_formatted = ",".join(f"'{x}'" for x in snapshot_shas)

        statement = sqlalchemy.text(
            "SELECT snapshot_sha "
            "FROM snapshots "
            "WHERE snapshot_num IN "
            "(SELECT snapshot_num FROM snapshots "
            f"WHERE snapshot_sha IN ({snapshot_shas_formatted})) AND "
            f"external={private}"
        )
        # Specify the columns for SQLAlchemy ORM mapping.
        statement = statement.columns(
            models.Snapshots.snapshot_sha,
        )

        query = self._session.query(models.Snapshots).from_statement(statement)
        snapshots = self._execute_query(query)

        return [x.snapshot_sha for x in snapshots]

    def query_binhosts(
        self,
        gs_bucket_name: str,
        snapshot_shas: List[str],
        build_target_profile_id: int,
        private: bool,
    ) -> List[Optional[models.Binhosts]]:
        """Query and return binhosts based on the filter parameters.

        Execute a custom query to filter binhosts.

        Args:
            gs_bucket_name: Name of the google storage bucket which contains the
                binhosts (e.g. "chromeos-prebuilts" in
                gs://chromeos-prebuilts/binhosts/..).
            snapshot_shas: List of snapshot SHAs of the binhosts.
            build_target_profile_id: Ids of the build target profiles of the
                binhosts.
            private: True if the binhosts are private.

        Returns:
            A list of binhost records, each containing the `binhost_id`,
            `gs_uri` and `created_at` fields. The list could be empty if there
            are no matching binhosts.

        Raises:
            DBError: When the sql query fails.
        """
        # Construct string of snapshot SHAs, to be used in the SQL query.
        snapshot_shas_formatted = ",".join(f"'{x}'" for x in snapshot_shas)

        statement = sqlalchemy.text(
            "SELECT binhost_id, gs_uri, "
            "EXTRACT(EPOCH FROM created_at) AS created_at "
            "FROM binhosts "
            f"WHERE gs_bucket_name='{gs_bucket_name}' AND "
            f"snapshot_sha IN ({snapshot_shas_formatted}) AND "
            f"build_target_profile_id={build_target_profile_id} AND "
            f"private={private} "
            "ORDER BY created_at DESC"
        )
        # Specify the columns for SQLAlchemy ORM mapping.
        statement = statement.columns(
            models.Binhosts.binhost_id,
            models.Binhosts.gs_uri,
            models.Binhosts.created_at,
        )
        query = self._session.query(models.Binhosts).from_statement(statement)

        return self._execute_query(query)

    def update_binhosts_last_accessed(self, binhost_ids: List[int]) -> None:
        """Update the `last_accessed` column to the current timestamp.

        Args:
            binhost_ids: List of binhost IDs.

        Raises:
            DBError: When the sql execution fails.
        """
        # Construct string of binhost IDs, to be used in the SQL query.
        binhost_ids_formatted = ",".join(f"{x}" for x in binhost_ids)

        statement = sqlalchemy.text(
            "UPDATE binhosts "
            "SET last_accessed = CURRENT_TIMESTAMP "
            f"WHERE binhost_id IN ({binhost_ids_formatted})"
        )

        try:
            self._session.execute(statement)
            self._session.close()
        except sqlalchemy.exc.DBAPIError as sql_error:
            raise DBError(
                "Error when executing the sql statement."
            ) from sql_error

# Copyright 2023 The ChromiumOS Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""Model definitions for SQLAlchemy ORM mapping between tables and objects."""

# pylint: disable=import-error
import sqlalchemy
from sqlalchemy import sql
from sqlalchemy.ext import declarative


# pylint: enable=import-error

Base = declarative.declarative_base()


class Versions(Base):
    """Store versions of database schemas."""

    __tablename__ = "versions"
    version = sqlalchemy.Column(sqlalchemy.INTEGER, primary_key=True)
    name = sqlalchemy.Column(sqlalchemy.VARCHAR(64))
    timestamp = sqlalchemy.Column(
        sqlalchemy.TIMESTAMP, server_default=sql.func.now()
    )


class Snapshots(Base):
    """Store data related to snapshots."""

    __tablename__ = "snapshots"
    snapshot_sha = sqlalchemy.Column(sqlalchemy.VARCHAR(40), primary_key=True)
    snapshot_num = sqlalchemy.Column(sqlalchemy.INTEGER, nullable=False)
    external = sqlalchemy.Column(sqlalchemy.BOOLEAN, nullable=False)
    buildbucket_id = sqlalchemy.Column(sqlalchemy.BIGINT, nullable=False)
    created_at = sqlalchemy.Column(sqlalchemy.TIMESTAMP)


class BuildTargetProfiles(Base):
    """Store all build targets and their profiles."""

    __tablename__ = "build_target_profiles"
    build_target_profile_id = sqlalchemy.Column(
        sqlalchemy.INTEGER, primary_key=True
    )
    build_target = sqlalchemy.Column(sqlalchemy.VARCHAR(128), nullable=False)
    profile = sqlalchemy.Column(sqlalchemy.VARCHAR(128), nullable=False)


class Binhosts(Base):
    """Store data related to binhosts."""

    __tablename__ = "binhosts"
    binhost_id = sqlalchemy.Column(sqlalchemy.BIGINT, primary_key=True)
    build_target_profile_id = sqlalchemy.Column(
        sqlalchemy.INTEGER,
        sqlalchemy.ForeignKey("build_target_profiles.build_target_profile_id"),
        nullable=False,
    )
    snapshot_sha = sqlalchemy.Column(
        sqlalchemy.VARCHAR(40), sqlalchemy.ForeignKey("snapshots.snapshot_sha")
    )
    gs_bucket_name = sqlalchemy.Column(sqlalchemy.TEXT, nullable=False)
    gs_uri = sqlalchemy.Column(sqlalchemy.TEXT, nullable=False)
    buildbucket_id = sqlalchemy.Column(sqlalchemy.BIGINT, nullable=False)
    complete = sqlalchemy.Column(
        sqlalchemy.BOOLEAN, nullable=False, default=True
    )
    private = sqlalchemy.Column(sqlalchemy.BOOLEAN, nullable=False)
    last_accessed = sqlalchemy.Column(sqlalchemy.TIMESTAMP)
    created_at = sqlalchemy.Column(sqlalchemy.TIMESTAMP)

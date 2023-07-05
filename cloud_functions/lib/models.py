# Copyright 2023 The ChromiumOS Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""Model definitions for SQLAlchemy ORM mapping between tables and objects."""

# pylint: disable=import-error
from sqlalchemy import BIGINT
from sqlalchemy import BOOLEAN
from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import INTEGER
from sqlalchemy import TEXT
from sqlalchemy import TIMESTAMP
from sqlalchemy import VARCHAR
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func


# pylint: enable=import-error

Base = declarative_base()


class Versions(Base):
    """Store versions of database schemas."""

    __tablename__ = "versions"
    version = Column(INTEGER, primary_key=True)
    name = Column(VARCHAR(64))
    timestamp = Column(TIMESTAMP, server_default=func.now())


class Snapshots(Base):
    """Store data related to snapshots."""

    __tablename__ = "snapshots"
    snapshot_sha = Column(VARCHAR(40), primary_key=True)
    snapshot_num = Column(INTEGER, nullable=False)
    external = Column(BOOLEAN, nullable=False)
    buildbucket_id = Column(BIGINT, nullable=False)
    created_at = Column(TIMESTAMP)


class BuildTargetProfiles(Base):
    """Store all build targets and their profiles."""

    __tablename__ = "build_target_profiles"
    build_target_profile_id = Column(INTEGER, primary_key=True)
    build_target = Column(VARCHAR(128), nullable=False)
    profile = Column(VARCHAR(128), nullable=False)


class Binhosts(Base):
    """Store data related to binhosts."""

    __tablename__ = "binhosts"
    binhost_id = Column(BIGINT, primary_key=True)
    build_target_profile_id = Column(
        INTEGER,
        ForeignKey("build_target_profiles.build_target_profile_id"),
        nullable=False,
    )
    snapshot_sha = Column(VARCHAR(40), ForeignKey("snapshots.snapshot_sha"))
    gs_bucket_name = Column(TEXT, nullable=False)
    gs_uri = Column(TEXT, nullable=False)
    buildbucket_id = Column(BIGINT, nullable=False)
    complete = Column(BOOLEAN, nullable=False, default=True)
    private = Column(BOOLEAN, nullable=False)
    last_accessed = Column(TIMESTAMP)
    created_at = Column(TIMESTAMP)

# Copyright 2023 The ChromiumOS Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""Unit tests for secret_manager."""

from google.cloud import secretmanager  # pylint: disable=import-error

from lib import constants
from lib import secret_manager


class MockSecretManagerServiceClient:
    """Class to mock a SecretManagerServiceClient instance."""

    def __init__(self, secret: str) -> None:
        self.secret = secret

    def access_secret_version(self, request: str) -> str:
        name = f"projects/{constants.PROJECT_ID}/secrets/{self.secret}/versions/latest"  # pylint: disable=line-too-long
        assert request == name
        return self.secret


def testEnvironmentStaging(monkeypatch):
    """Test the environment is set to staging."""
    monkeypatch.setenv("ENV", "staging")

    secrets = secret_manager.LookupServiceDbSecrets()

    assert secrets.env == "staging"


def testGetDatabaseName(monkeypatch):
    """Test the correct database name is returned."""
    test_db_name = "test-db-name"

    def mock_access_secret_version(*_args, **_kwargs):
        return MockSecretManagerServiceClient(secret=test_db_name)

    monkeypatch.setattr(
        secret_manager.LookupServiceDbSecrets, "database_name", test_db_name
    )
    monkeypatch.setattr(
        secretmanager, "SecretManagerServiceClient", mock_access_secret_version
    )

    secrets = secret_manager.LookupServiceDbSecrets()

    assert secrets.database_name == test_db_name


def testGetUser(monkeypatch):
    """Test the correct user is returned."""
    test_db_user = "test-db-user"

    def mock_access_secret_version(*_args, **_kwargs):
        return MockSecretManagerServiceClient(secret=test_db_user)

    monkeypatch.setattr(
        secret_manager.LookupServiceDbSecrets, "user", test_db_user
    )
    monkeypatch.setattr(
        secretmanager, "SecretManagerServiceClient", mock_access_secret_version
    )

    secrets = secret_manager.LookupServiceDbSecrets()

    assert secrets.user == test_db_user


def testGetPassword(monkeypatch):
    """Test the correct password is returned."""
    test_db_pw = "test-db-pw"

    def mock_access_secret_version(*_args, **_kwargs):
        return MockSecretManagerServiceClient(secret=test_db_pw)

    monkeypatch.setattr(
        secret_manager.LookupServiceDbSecrets, "password", test_db_pw
    )
    monkeypatch.setattr(
        secretmanager, "SecretManagerServiceClient", mock_access_secret_version
    )

    secrets = secret_manager.LookupServiceDbSecrets()

    assert secrets.password == test_db_pw


def testGetDatabaseHost(monkeypatch):
    """Test the correct database host is returned."""
    test_db_host = "100.100.1.1"

    def mock_access_secret_version(*_args, **_kwargs):
        return MockSecretManagerServiceClient(secret=test_db_host)

    monkeypatch.setattr(
        secret_manager.LookupServiceDbSecrets, "database_host", test_db_host
    )
    monkeypatch.setattr(
        secretmanager, "SecretManagerServiceClient", mock_access_secret_version
    )

    secrets = secret_manager.LookupServiceDbSecrets()

    assert secrets.database_host == test_db_host


def testGetDatabasePort(monkeypatch):
    """Test the correct database host is returned."""
    test_db_port = 123

    def mock_access_secret_version(*_args, **_kwargs):
        return MockSecretManagerServiceClient(secret=test_db_port)

    monkeypatch.setattr(
        secret_manager.LookupServiceDbSecrets, "database_port", test_db_port
    )
    monkeypatch.setattr(
        secretmanager, "SecretManagerServiceClient", mock_access_secret_version
    )

    secrets = secret_manager.LookupServiceDbSecrets()

    assert secrets.database_port == test_db_port

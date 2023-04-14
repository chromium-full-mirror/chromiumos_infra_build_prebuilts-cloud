# Copyright 2023 The ChromiumOS Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""Unit tests for the config module."""

import pytest

from lib import config


def test_get(mock_config_reader: config.ConfigReader):
    """Test the getter method of the config module."""
    assert (
        mock_config_reader.get("topics")["update_snapshot_data"]
        == "test_topic_update_snapshot_data"
    )

    # Modify the returned dict and assert that the actual config values are not
    # changed.
    config_topics = mock_config_reader.get("topics")
    config_topics["update_snapshot_data"] = "new_topic"
    assert (
        mock_config_reader.get("topics")["update_snapshot_data"]
        == "test_topic_update_snapshot_data"
    )


def test_get_key_error(mock_config_reader: config.ConfigReader):
    """Test the getter method of the config module with an invalid key."""
    with pytest.raises(KeyError):
        mock_config_reader.get("random")

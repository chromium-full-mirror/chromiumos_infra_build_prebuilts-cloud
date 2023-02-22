# Copyright 2023 The ChromiumOS Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import sys

import pytest


if __name__ == "__main__":
    return_code = pytest.main(["--disable-warnings"])
    sys.exit(return_code)

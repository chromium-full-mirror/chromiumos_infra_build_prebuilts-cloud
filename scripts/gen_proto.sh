#!/bin/bash

# Copyright 2023 The ChromiumOS Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""Script to compile proto files."""

protoc -I /mnt/host/source/infra/proto/src/ \
  --python_out \
  /mnt/host/source/infra/build/prebuilts-cloud/cloud_functions/protobuf \
  --proto_path /mnt/host/source/infra/proto/src/ \
  /mnt/host/source/infra/proto/src/chromiumos/prebuilts_cloud.proto

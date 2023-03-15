#!/bin/bash
# Copyright 2023 The ChromiumOS Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

# Invoke the local cloud function.

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SOURCE_FILE="${DIR}/../cloud_functions/main.py"

# Load default env variables.
echo "Loading env variables from '${DIR}/.env.defaults'."
source "${DIR}/.env.defaults"


# Override env variables if .env.local is present.
if [ -f "${DIR}/.env.local" ]; then
  echo "Overriding env variables using '${DIR}/.env.local'."
  source "${DIR}/.env.local"
fi

PAYLOAD_FILE="$DIR/local_payload.json"

curl -X POST \
    -H 'Content-type: application/json' \
    -d "@${PAYLOAD_FILE}" \
    "http://localhost:${FUNCTION_PORT}"
echo

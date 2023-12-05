#!/bin/bash
# Copyright 2023 The ChromiumOS Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

# Setup a python virtual env, install required packages and run the cloud
# function server.

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Load default env variables.
echo "Loading env variables from '${DIR}/.env.defaults'."
source "${DIR}/.env.defaults"


# Override env variables if .env.local is present.
if [ -f "${DIR}/.env.local" ]; then
  echo "Overriding env variables using '${DIR}/.env.local'."
  source "${DIR}/.env.local"
fi

SOURCE_PATH="${DIR}/../cloud_functions/${FUNCTION_SOURCE_FILE}.py"
VENV_DIR="${DIR}/../venv"

# Setup virtual env.
if [[ -d "${VENV_DIR}" ]]; then
  echo "Found python virtual environment directory: ${VENV_DIR}"
else
  echo "Creating python virtual environment: ${VENV_DIR}"
  "python3" -m venv "${VENV_DIR}"
fi
# shellcheck source=../venv/bin/activate
source "${VENV_DIR}/bin/activate"
pip install --require-hashes -r "${DIR}/../cloud_functions/requirements.txt"

# Start the cloud function server.
functions-framework \
  --source="${SOURCE_PATH}" \
  --target="${FUNCTION_TARGET}" \
  --signature-type="${FUNCTION_SIGNATURE_TYPE}" \
  --port="${FUNCTION_PORT}" \
  --debug

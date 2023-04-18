#!/bin/bash
# Copyright 2023 The ChromiumOS Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

# Invoke the local cloud function.
#
# Command line args:
# -r: request type, can be one of [lookup, update].
#
# Different ways to run this script:
# 1) First, create a `scripts/query_params.txt` file containing the query
#    string. e.g. data='123'&type='abc'
#    Then, run `./scripts/test_cloud_function_local.sh -r lookup`
#    This will invoke the lookup_service function as a GET request.
#
# 2) First, create a `scripts/local_payload.json` file containing the payload,
#    see `scripts/example_payload.json` for reference.
#    Then, run `./scripts/test_cloud_function_local.sh` -r update`
#    This will invoke  the update_service function as a POST request with the
#    payload from `scripts/local_payload.json`.

RED='\033[0;31m'

# Log error messages.
err() {
  # shellcheck disable=SC2059
  printf "${RED}[$(date +'%Y-%m-%dT%H:%M:%S%z')]: $*\n" >&2
  exit 1
}

# Parse command line args.
while getopts ":r:" opt; do
  case ${opt} in
    r) request_type="${OPTARG}" ;;
    \?) err "Invalid option -${OPTARG}"
  esac
done

# Validate command line args.
case ${request_type} in
  lookup);;
  update);;
  *) err "Invalid request_type provided! Acceptable values: lookup, update."
esac

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Load default env variables.
echo "Loading env variables from '${DIR}/.env.defaults'."
source "${DIR}/.env.defaults"


# Override env variables if .env.local is present.
if [ -f "${DIR}/.env.local" ]; then
  echo "Overriding env variables using '${DIR}/.env.local'."
  source "${DIR}/.env.local"
fi

# Invoke the function based on the request type.
if [[ "${request_type}" == "lookup" ]]; then
  params_file_path="${DIR}/query_params.txt"
  # Check for scripts/query_params.txt
  if [[ ! -f "${params_file_path}" ]]; then
    err "To invoke the lookup service, create a scripts/query_params.txt file."
  fi
  query_params=$(<"${DIR}/query_params.txt")
  curl -X GET "http://localhost:${FUNCTION_PORT}?${query_params}"
  echo
elif [ "${request_type}" == "update" ]; then
  PAYLOAD_FILE="${DIR}/local_payload.json"
  # Check for scripts/local_payload.json
  if [ ! -f "${PAYLOAD_FILE}" ]; then
    err "To invoke the update service, create a scripts/local_payload.json \
file."
  fi

  curl -X POST \
    -H 'Content-type: application/json' \
    -d "@${PAYLOAD_FILE}" \
    "http://localhost:${FUNCTION_PORT}"
  echo
else
  err "request type: ${request_type} is an unexpected value"
fi

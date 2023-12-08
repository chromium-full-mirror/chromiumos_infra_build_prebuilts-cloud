#!/usr/bin/env bash
# Copyright 2023 The ChromiumOS Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

# Script to deploy `update_service` cloud functions
# (e.g. update-service-snapshot-data).

# Path to the env file for the cloud function.
:"${ENV_FILE:=}"

# Cloud function name.
:"${FUNCTION_NAME:=}"

# Runtime service account for the cloud function.
:"${SERVICE_ACCOUNT:=}"

# PubSub topic which will act as a trigger to the cloud function.
:"${TOPIC_NAME:=}"

# VPC connector to be associated with the cloud function.
:"${VPC_CONNECTOR:=}"

# Deploy the cloud function.
gcloud functions deploy "${FUNCTION_NAME}" \
--egress-settings=private-ranges-only --entry-point=update_service \
--env-vars-file="${ENV_FILE}" --gen2 \
--ingress-settings=internal-only --region=us-central1 --retry \
--runtime=python38 --service-account="${SERVICE_ACCOUNT}" \
--source=cloud_functions/. --trigger-topic="${TOPIC_NAME}" \
--vpc-connector="${VPC_CONNECTOR}"

# For gen2 cloud functions with an eventarc trigger, the corresponding PubSub
# subscription is automatically created when the cloud function is deployed. To
# update the subscription parameters, get the name of the generated subscription
# and update it using gcloud cli commands.
trigger_name=$(gcloud functions describe "${FUNCTION_NAME}" \
--region=us-central1 --format='value(eventTrigger.trigger)')

trigger_subscription=$(gcloud eventarc triggers describe "${trigger_name}" \
--location us-central1 --format='value(transport.pubsub.subscription)')

gcloud pubsub subscriptions update "${trigger_subscription}" \
--retain-acked-messages --message-retention-duration=7d

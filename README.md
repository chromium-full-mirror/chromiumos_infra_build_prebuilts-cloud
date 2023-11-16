# The CrOS Build Prebuilts Cloud Repo

This repo houses all the GCP code for the `chromeos-prebuilts` project.

## Cloud Functions

We're using Cloud Functions as a serverless platform for the lookup service.

The entry points for the Cloud Functions are defined in `cloud_functions/main.py`.
Each entry point has a `functions_framework` decorator which helps receive the function
arguments based on the signature type specified.

### Deployment

**During initial development, we are manually deploying changes to the `staging` instances of both Cloud SQL and Cloud Functions.
DO NOT deploy to production instances as the production deployment process will be automated later.**

Creating Cloud Functions via the Google Cloud console:

1. Go to `Cloud Functions` and click on `Create function`.
2. Select `Environment=2nd gen`, enter a function name.
3. For event driven functions which need to be triggered from Pub/Sub messages:
    - Note: The cloud function must be created after the topic has been created.
        Since each cloud function can only have one trigger, in cases where we
        have the same function entry point to consume messages from different
        Pub/Sub topics, create multiple cloud functions, one for each topic.
    - Click on `Add EventArc Trigger` and select `Trigger type=Google sources`, `Event provider=Cloud Pub/Sub` and `Event=google.cloud.pubsub.topic.v1.messagePublished`.
    - Select the Pub/Sub topic and select the `prebuilts-cloud` service account.
    - Check the `Retry on failure` box. This ensures that the message is processed again when there's an error.
4. Enter configuration settings such as runtime env variables and connection settings to enable routing through the VPC connector.


There are two ways to manually deploy additional changes:

Option 1: Create and upload a zip of the source code (Recommended)

1. Work on changes locally like normal development.
2. Once ready, in `cloud_functions/`, run `zip -r <date>-<version>.zip .` (Example: `zip -r 02072023-1.zip .`)
3. Upload the .zip file to Cloud Storage in the `cloudfunctions-manual-deployments` [bucket](https://pantheon.corp.google.com/storage/browser/cloudfunctions-manual-deployments?project=chromeos-prebuilts).
4. In Cloud Functions, [select](https://pantheon.corp.google.com/functions/details/us-central1/staging-lookup-service?env=gen1&project=chromeos-prebuilts) the `staging-lookup-service` to Edit.
5. In Step 1, Configuration, edit settings if needed.
6. In Step 2, Code, select `ZIP from Cloud Storage` for the `Source code` and select the .zip file uploaded in Step 3 above.
7. Select `Deploy` and wait a few minutes. If the deployment fails, take a look at the logs and make adjustments as needed.

Option 2: Use the Cloud Functions Inline Editor (Not Recommended)

1. In Cloud Functions, [select](https://pantheon.corp.google.com/functions/details/us-central1/staging-lookup-service?env=gen1&project=chromeos-prebuilts) the `staging-lookup-service` to Edit.
2. In Step 1, Configuration, edit settings if needed.
3. In Step 2, Code, make changes directly using the Inline Editor provided.
4. Select `Deploy` and wait a few minutes. If the deployment fails, take a look at the logs and make adjustments as needed.

#### Runtime environment variables for the lookup service cloud function:

- ENV : Environment, can be one of staging, prod.
- PREBUILTS_SQL_INSTANCE_HOST : IP address for the prebuilts cloud sql instance.
- PREBUILTS_SQL_INSTANCE_PORT : port for the prebuilts cloud sql instance.

### General Testing

The main way to test deployed Cloud Functions via a [trigger](https://cloud.google.com/functions/docs/calling) including HTTP requests and Pub/Sub. `staging-lookup-service` is setup to accept HTTP triggers via the `main` function. A function cannot have more than one trigger associated with it, but a trigger can be associated with many functions (as long as the functions are unique).

To test `staging-lookup-service`, go to the `Testing` [tab](https://pantheon.corp.google.com/functions/details/us-central1/staging-lookup-service?env=gen1&project=chromeos-prebuilts&tab=testing) and click `Test the Function`. Output is only available if the Cloud Function is deployed using `1st gen` environment.

### Local testing and development

To develop and test cloud functions locally, we should be able to connect to the cloud sql instance from our local machine/cloudtop. Hence, `Public IP` has been enabled on the `prebuilts-staging` instance to accommodate this and the database can be accessed locally through cloud sql auth proxy. **Public IP should not be enabled in production.**

Note: We are running the cloud function locally but are using GCP's staging environment, including staging Cloud SQL database and Secret Manager instances.

Steps to run cloud functions locally (All of these steps are done outside the chroot):
- Setup [cloud sql auth proxy](https://cloud.google.com/sql/docs/postgres/connect-auth-proxy):
    - Follow the steps [here](https://cloud.google.com/sql/docs/postgres/sql-proxy#install) to download and install Cloud SQL Auth proxy.
    - Add the downloaded `cloud-sql-proxy` to your `$PATH`.
    - Start the auth proxy:
        ```
        $cloud-sql-proxy --address 127.0.0.1 --port 5432 chromeos-prebuilts:us-central1:prebuilts-staging
        ```
    - The database should now be accessible locally through the proxy.
- Install [functions-framework](https://pypi.org/project/functions-framework/).
- The default values for env variables are in the `scripts/.env.defaults` file. Add a `scripts/.env.local` file to override the values. This can be helpful for local testing without checking it into the repo. Env variables used:
    - FUNCTION_SOURCE_FILE : Source file for the cloud function.
    - FUNCTION_TARGET : Entry point for the cloud function.
    - FUNCTION_PORT : Port to run the function on.
    - FUNCTION_SIGNATURE_TYPE : Signature type of the function, which determines
        the event format. Can be one of http, event or cloudevent.
    - ENV : environment, can be one of staging, prod.
    - PREBUILTS_SQL_INSTANCE_HOST : IP address for the sql instance.
    - PREBUILTS_SQL_INSTANCE_PORT : Port for the sql instance.
    - TOPIC_NAME_UPDATE_SNAPSHOT_DATA : Topic name of the update snapshot data Pub/Sub topic.
        Topic name refers to the complete name that uniquely identifies a Pub/Sub topic.
    - TOPIC_NAME_UPDATE_BINHOST_DATA : Topic name of the update binhost data Pub/Sub topic.
- Run the cloud function server locally : `./scripts/run_server_local.sh` (This script also sets up a virtual env and installs the required packages).
    - In `.env.local`, update `FUNCTION_TARGET` and `FUNCTION_SIGNATURE_TYPE` based on whether you want to run the lookup or the update service.
    - For running the lookup function, `FUNCTION_TARGET=lookup_service` and `FUNCTION_SIGNATURE_TYPE=http`
    - For running the update function, `FUNCTION_TARGET=update_service` and `FUNCTION_SIGNATURE_TYPE=cloud_event`
- Invoke the cloud function locally : `./scripts/test_cloud_function_local.sh -r lookup`
    - Suitable command line args need to be passed to call the lookup/update
    service with the required inputs.
    - More details in the `./scripts/test_cloud_function_local.sh` file.

Note: The cloud function auto restarts when any of the source files are changed.

### Unit Testing

We use [pytest](https://docs.pytest.org/en/7.2.x/) as our unittesting framework and [VPython](https://chromium.googlesource.com/infra/infra/+/main/doc/users/vpython_one_page.md) to run unittests in a Python VirtualEnv. See [here](https://chromium.googlesource.com/infra/infra/+/main/infra/tools/dockerbuild/wheels.md) for a list of available wheels. `vpython3 run_tests.py` will run all unittests by default.

## Cloud SQL

We have two Cloud SQL instances:

1. `prebuilts` - the production instance
2. `prebuilts-staging` - the staging instance

### Databases

Each instance currently contains a `lookup_service` database for the project.

### Deployments

**During initial development, we are manually deploying changes to the `staging` instances of both Cloud SQL and Cloud Functions.
DO NOT deploy to production instances as the production deployment process will be automated later.**

To manually deploy changes:

1. Upload the .sql file to Cloud Storage in the `cloudsql-manual-deployments` [bucket](https://pantheon.corp.google.com/storage/browser/cloudsql-manual-deployments?project=chromeos-prebuilts).
2. In the Cloud SQL instance [overview page](https://pantheon.corp.google.com/sql/instances/prebuilts-staging/overview?project=chromeos-prebuilts), select `IMPORT`.
3. Select the .sql file uploaded to Cloud Storage above and select `lookup_service` as the database destination.
4. Select `Import` and wait a few minutes for the import to complete.

### Connections

The following steps can be used to connect to the database and verify deployments and/or query data:

1. SSH to the VM [instance](https://pantheon.corp.google.com/compute/instances?onCreate=true&project=chromeos-prebuilts) created for the project.
2. Open (2) SSH connections to the `cloudsql-connection` instance.
3. In the (1) SSH-in-browser window, run `./cloud_sql_proxy -instances=chromeos-prebuilts:us-central1:prebuilts-staging=tcp:5432`.
4. In the (2) SSH-in-browser window, run `psql "host=127.0.0.1 port=5432 sslmode=disable dbname=lookup_service user=postgres"`.
5. The postgres user password can be found [here](https://pantheon.corp.google.com/security/secret-manager?project=chromeos-prebuilts).

## Pub/Sub

We're using [Pub/Sub](https://cloud.google.com/pubsub/docs/overview) to receive messages and update metadata for snapshots, binhosts, etc in the database.
The `update_service` cloud functions receive messages as cloud events through Pub/Sub subscriptions via EventArc triggers. Each use case has its own
Pub/Sub topic (e.g. update_snapshot_data, update_binhost_data) and the corresponding cloud function processes the messages, performs database operations.
With 2nd gen cloud functions, each function can only have one trigger. So each Pub/Sub topic has its own cloud function for processing messages.

### Deployment

**During initial development, we are manually creating Pub/Sub schemas, topics and corresponding subscriptions via Google Cloud console.
DO NOT deploy to production instances as the production deployment process will be automated later.**

Steps for setting up Pub/Sub topics (this needs to be done for each topic):

1. In Google Cloud console, go to `Pub/Sub`.
2. Create Schema (used for validating Pub/Sub message format):
    - Go to `Schemas` and click `Create Schema`.
    - Type a Schema ID and select `Schema type=Protocol Buffer`.
    - Enter the protocol buffer definition for this schema and create the schema.
    - Note: The same protobuf schema definition is used in the `update_service` cloud function to consume messages from this topic.
3. Create Pub/Sub topic:
    - Go to `Topics` and click `Create topic`.
    - Type a Topic ID and check the `Use a schema` box, select the previously created schema and encoding `type=Binary`. Select the `Enable message retention` box with `Days=7`.
    - Use the default `Google-managed encryption key`.
4. Trigger for the `update_service` cloud function:
    - When creating the cloud function, an `Eventarc trigger` is enabled with the corresponding topic, so the subscription is automatically created with this step.


## Protocol Buffers

We're using protocol buffers to have a consistent data format when sending, retrieving Pub/Sub messages.

- The proto definition file related to Pub/Sub is located [here](https://source.chromium.org/chromiumos/chromiumos/codesearch/+/main:infra/proto/src/chromiumos/prebuilts_cloud.proto).
- The `scripts/gen_proto.sh` script compiles and puts the generated proto files in `cloud_functions/protobuf/chromiumos/`.


## Binhost Lookup Service API

The binhost lookup service is a HTTP GET endpoint running in a cloud function. The protocol buffer definitions for the request and response are defined in [prebuilts_cloud.proto](https://source.chromium.org/chromiumos/chromiumos/codesearch/+/main:infra/proto/src/chromiumos/prebuilts_cloud.proto).

The query parameter to be sent with the request:
- "filter": A `LookupBinhostsRequest` object encoded as a URL safe base64 byte object.

The response is a `LookupBinhostsResponse` object encoded as a URL safe base64 byte object, sent in the response body.

## Secret Manager

GCP Secret Manager is used to store sensitive information that can be accessed by the cloud functions. The secrets are created and managed manually through the cloud console. Secrets being used:
- prebuilts-db:      Name of the prebuilts PostgreSQL instance.
- prebuilts-db-user: Name of the database user.
- prebuilts-db-pw  : Password for the database user.

NOTE: Name of each of these secrets is prefixed by the environment name. e.g. staging-prebuilts-db

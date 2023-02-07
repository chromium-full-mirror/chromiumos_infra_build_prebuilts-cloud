# The CrOS Build Prebuilts Cloud Repo

This repo houses all the GCP code for the `chromeos-prebuilts` project.

## Cloud Functions

We're using Cloud Functions as a serverless platform for the lookup service.

### Deployment

**During initial development, we are manually deploying changes to the `staging` instances of both Cloud SQL and Cloud Functions.
DO NOT deploy to production instances as the production deployment process will be automated later.**

There are two ways to manually deploy changes:

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

### General Testing

The main way to test deployed Cloud Functions via a [trigger](https://cloud.google.com/functions/docs/calling) including HTTP requests and Pub/Sub. `staging-lookup-service` is setup to accept HTTP triggers via the `main` function. A function cannot have more than one trigger associated with it, but a trigger can be associated with many functions (as long as the functions are unique).

To test `staging-lookup-service`, go to the `Testing` [tab](https://pantheon.corp.google.com/functions/details/us-central1/staging-lookup-service?env=gen1&project=chromeos-prebuilts&tab=testing) and click `Test the Function`. Output is only available if the Cloud Function is deployed using `1st gen` environment.

### Unit Testing

TODO.

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
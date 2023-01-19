# The CrOS Build Prebuilts Cloud Repo

This repo houses all the GCP code for the `chromeos-prebuilts` project.

## Cloud SQL

We have two Cloud SQL instances:

1. `prebuilts` - the production instance
2. `prebuilts-staging` - the staging instance

### Databases

Each instance currently contains a `lookup_service` database for the project.

### Deployments

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
5. The postgres user password can be found [here](https://valentine.corp.google.com/#/show/1674164197911673?tab=metadata).
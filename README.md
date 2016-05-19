zscore
======

A sleeping competition app, at [zscore.mit.edu](https://zscore.mit.edu).

Dev setup
---------

1. `git clone git@github.com:sleepers-anonymous/zscore.git ; cd zscore`
2. `make deps` (If you really don't want to deploy ever, you can just do `make dev_deps`.)
3. `./manage.py migrate`
4. `make serve`, then go to `localhost:8000`

Deploying to prod
-----------------

zScore runs on Google App Engine.

1. Ask someone for access to the GCP project.
2. Create a `zscore/secrets.py` file with a `SECRET_KEY` setting (ask someone for the value).
3. `make deploy`.

If you screw something up, head over to the [Google Cloud Console](https://console.cloud.google.com), click on "App Engine", then "Versions", and move traffic back to the previous version.

To see logs, go to the [Google Cloud Console](https://console.cloud.google.com), click on "Logging".  `request_log` is what it sounds like; `stderr` has error tracebacks.

### Advanced options

To deploy only static assets (which go in the zscore-static bucket on Google Cloud Storage), `make gcs_deploy`.  To deploy only dynamic files (which go to App Engine), `make gae_deploy`.  These two are independent; `make deploy` runs both.

To run your dev server against the live DB, grab the [Cloud SQL proxy](https://cloud.google.com/sql/docs/sql-proxy) and put it on your path in a file called `cloud_sql_proxy`.  Follow the instructions at that link to create a service account for your dev server, and save the key in `.cloud-sql.key`.  Now run `make proxy` to start the proxy, and `PROD_DB=1 ./manage.py shell_plus` to start a shell.

serve: dev_deps
	./manage.py runserver_plus

deploy: gae_deploy gcs_deploy ;

deps: dev_deps deploy_deps ;

proxy:
	if ! type gcloud >/dev/null ; then \
		echo "Please install the Cloud SQL proxy from https://cloud.google.com/sql/docs/sql-proxy" ; exit 1 ; fi
	cloud_sql_proxy -dir /tmp/cloudsql -instances=zscoresleep:us-east1:zscore-sql-1 -credential_file .cloud-sql.key

dev_deps:
	# TODO(benkraft): separate dev and prod requirements files
	# TODO(benkraft): ensure we're in a venv
	pip install -r requirements.txt

deploy_deps:
	if ! type gcloud >/dev/null ; then \
		echo "Please install gcloud from https://cloud.google.com/sdk/" ; exit 1 ; fi
	if ! gcloud components update 2>/dev/null ; then \
		echo "updates failed, try running 'gcloud components update' manually" ; exit 1 ; fi
	type gsutil >/dev/null || gcloud components install gsutil

gcs_deploy: deploy_deps
	yes yes | ./manage.py collectstatic
	gsutil rsync -R zscore/static/ gs://zscore-static/

gae_deploy: deploy_deps
	# TODO(benkraft): actually check that it has the right values.
	if ! [ -f zscore/secrets.py ] ; then \
		echo "Please create a zscore/secrets.py with a SECRET_KEY setting." ; exit 1 ; fi
	gcloud preview app deploy --promote --stop-previous-version --project zscoresleep

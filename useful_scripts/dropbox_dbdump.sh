#!/bin/bash

date=`date +"%d-%m-%Y"`
# Output to dropbox in archive format
pg_dump -f ${HOME}/Dropbox/dbdump/zscore_db_${date}.sql -F tar
# Check that dropbox is running
pgrep dropbox >/dev/null || ${HOME}/.dropbox-dist/dropboxd

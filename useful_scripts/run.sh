#! /bin/bash
export PYTHONIOENCODING=utf8
k5start -v -f /etc/krb5.keytab daemon/zscore.mit.edu

flock /tmp/ -c /zscore/useful_scripts/zephyrbot.py

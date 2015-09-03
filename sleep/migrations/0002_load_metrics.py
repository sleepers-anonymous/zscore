# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.core.management import call_command


def load_metrics():
    call_command('loaddata', 'metrics.json')


class Migration(migrations.Migration):

    dependencies = [
        ('sleep', '0001_initial'),
    ]

    operations = [
    ]

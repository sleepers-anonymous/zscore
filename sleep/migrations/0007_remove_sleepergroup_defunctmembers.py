# -*- coding: utf-8 -*-
# Generated by Django 1.9.1 on 2016-08-24 06:53
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('sleep', '0006_remove_sleep_sleepcycles'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='sleepergroup',
            name='defunctMembers',
        ),
    ]
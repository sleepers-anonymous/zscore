# -*- coding: utf-8 -*-
# Generated by Django 1.9.1 on 2016-08-24 06:42
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('sleep', '0005_auto_20160824_0235'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='sleep',
            name='sleepcycles',
        ),
    ]
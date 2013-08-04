# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'SleeperProfile.idealWakeupWeekend'
        db.add_column('sleep_sleeperprofile', 'idealWakeupWeekend',
                      self.gf('django.db.models.fields.TimeField')(default=datetime.time(9, 0)),
                      keep_default=False)

        # Adding field 'SleeperProfile.idealWakeupWeekday'
        db.add_column('sleep_sleeperprofile', 'idealWakeupWeekday',
                      self.gf('django.db.models.fields.TimeField')(default=datetime.time(8, 0)),
                      keep_default=False)

        # Adding field 'SleeperProfile.idealSleepTimeWeekend'
        db.add_column('sleep_sleeperprofile', 'idealSleepTimeWeekend',
                      self.gf('django.db.models.fields.TimeField')(default=datetime.time(0, 0)),
                      keep_default=False)

        # Adding field 'SleeperProfile.idealSleepTimeWeekday'
        db.add_column('sleep_sleeperprofile', 'idealSleepTimeWeekday',
                      self.gf('django.db.models.fields.TimeField')(default=datetime.time(23, 0)),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'SleeperProfile.idealWakeupWeekend'
        db.delete_column('sleep_sleeperprofile', 'idealWakeupWeekend')

        # Deleting field 'SleeperProfile.idealWakeupWeekday'
        db.delete_column('sleep_sleeperprofile', 'idealWakeupWeekday')

        # Deleting field 'SleeperProfile.idealSleepTimeWeekend'
        db.delete_column('sleep_sleeperprofile', 'idealSleepTimeWeekend')

        # Deleting field 'SleeperProfile.idealSleepTimeWeekday'
        db.delete_column('sleep_sleeperprofile', 'idealSleepTimeWeekday')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'sleep.allnighter': {
            'Meta': {'object_name': 'Allnighter'},
            'comments': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'date': ('django.db.models.fields.DateField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'sleep.friendrequest': {
            'Meta': {'object_name': 'FriendRequest'},
            'accepted': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'requestee': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'requestor': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['sleep.SleeperProfile']"})
        },
        'sleep.schoolorworkplace': {
            'Meta': {'object_name': 'SchoolOrWorkPlace'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'sleep.sleep': {
            'Meta': {'object_name': 'Sleep'},
            'comments': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'date': ('django.db.models.fields.DateField', [], {}),
            'end_time': ('django.db.models.fields.DateTimeField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'start_time': ('django.db.models.fields.DateTimeField', [], {}),
            'timezone': ('django.db.models.fields.CharField', [], {'default': "'America/New_York'", 'max_length': '255'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'sleep.sleeperprofile': {
            'Meta': {'object_name': 'SleeperProfile'},
            'emailreminders': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'follows': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'follows+'", 'blank': 'True', 'to': "orm['auth.User']"}),
            'friends': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'friends+'", 'blank': 'True', 'to': "orm['auth.User']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'idealSleep': ('django.db.models.fields.DecimalField', [], {'default': '7.5', 'max_digits': '4', 'decimal_places': '2'}),
            'idealSleepTimeWeekday': ('django.db.models.fields.TimeField', [], {'default': 'datetime.time(11, 0)'}),
            'idealSleepTimeWeekend': ('django.db.models.fields.TimeField', [], {'default': 'datetime.time(0, 0)'}),
            'idealWakeupWeekday': ('django.db.models.fields.TimeField', [], {'default': 'datetime.time(8, 0)'}),
            'idealWakeupWeekend': ('django.db.models.fields.TimeField', [], {'default': 'datetime.time(9, 0)'}),
            'privacy': ('django.db.models.fields.SmallIntegerField', [], {'default': '0'}),
            'privacyFriends': ('django.db.models.fields.SmallIntegerField', [], {'default': '0'}),
            'privacyLoggedIn': ('django.db.models.fields.SmallIntegerField', [], {'default': '0'}),
            'requested': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'requests'", 'blank': 'True', 'through': "orm['sleep.FriendRequest']", 'to': "orm['auth.User']"}),
            'timezone': ('django.db.models.fields.CharField', [], {'default': "'America/New_York'", 'max_length': '255'}),
            'use12HourTime': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['auth.User']", 'unique': 'True'})
        }
    }

    complete_apps = ['sleep']
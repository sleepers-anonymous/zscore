# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Metric.description'
        db.add_column('sleep_metric', 'description',
                      self.gf('django.db.models.fields.TextField')(default='', blank=True),
                      keep_default=False)

        # Adding field 'Metric.short_description'
        db.add_column('sleep_metric', 'short_description',
                      self.gf('django.db.models.fields.TextField')(default='', blank=True),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'Metric.description'
        db.delete_column('sleep_metric', 'description')

        # Deleting field 'Metric.short_description'
        db.delete_column('sleep_metric', 'short_description')


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
        'sleep.groupinvite': {
            'Meta': {'object_name': 'GroupInvite'},
            'accepted': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['sleep.SleeperGroup']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'sleep.grouprequest': {
            'Meta': {'object_name': 'GroupRequest'},
            'accepted': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['sleep.SleeperGroup']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'sleep.membership': {
            'Meta': {'object_name': 'Membership'},
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['sleep.SleeperGroup']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'privacy': ('django.db.models.fields.SmallIntegerField', [], {'default': '0'}),
            'role': ('django.db.models.fields.SmallIntegerField', [], {'default': '0'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'sleep.metric': {
            'Meta': {'ordering': "['-priority']", 'object_name': 'Metric'},
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'display_style': ('django.db.models.fields.CharField', [], {'default': "'asHHMM'", 'max_length': '6'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '40'}),
            'priority': ('django.db.models.fields.IntegerField', [], {'unique': 'True'}),
            'short_description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'show_by_default': ('django.db.models.fields.BooleanField', [], {'default': 'True'})
        },
        'sleep.partialsleep': {
            'Meta': {'object_name': 'PartialSleep'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'start_time': ('django.db.models.fields.DateTimeField', [], {}),
            'timezone': ('django.db.models.fields.CharField', [], {'default': "'America/New_York'", 'max_length': '255'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['auth.User']", 'unique': 'True'})
        },
        'sleep.schoolorworkplace': {
            'Meta': {'object_name': 'SchoolOrWorkPlace'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'sleep.sleep': {
            'Meta': {'object_name': 'Sleep'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'comments': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'date': ('django.db.models.fields.DateField', [], {}),
            'end_time': ('django.db.models.fields.DateTimeField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'quality': ('django.db.models.fields.SmallIntegerField', [], {'default': '4'}),
            'sleepcycles': ('django.db.models.fields.SmallIntegerField', [], {}),
            'start_time': ('django.db.models.fields.DateTimeField', [], {}),
            'timezone': ('django.db.models.fields.CharField', [], {'default': "'America/New_York'", 'max_length': '255'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'sleep.sleepergroup': {
            'Meta': {'object_name': 'SleeperGroup'},
            'defunctMembers': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'defunct+'", 'blank': 'True', 'to': "orm['auth.User']"}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'members': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'sleepergroups'", 'blank': 'True', 'through': "orm['sleep.Membership']", 'to': "orm['auth.User']"}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'privacy': ('django.db.models.fields.SmallIntegerField', [], {'default': '50'})
        },
        'sleep.sleeperprofile': {
            'Meta': {'object_name': 'SleeperProfile'},
            'autoAcceptGroups': ('django.db.models.fields.SmallIntegerField', [], {'default': '50'}),
            'emailActivated': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'emailSHA1': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'emailSHA1GenerationDate': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2013, 10, 18, 0, 0)'}),
            'emailTime': ('django.db.models.fields.TimeField', [], {'default': 'datetime.time(12, 0)'}),
            'emailreminders': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'follows': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'follows+'", 'blank': 'True', 'to': "orm['auth.User']"}),
            'friends': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'friends+'", 'blank': 'True', 'to': "orm['auth.User']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'idealSleep': ('django.db.models.fields.DecimalField', [], {'default': '7.5', 'max_digits': '4', 'decimal_places': '2'}),
            'idealSleepTimeWeekday': ('django.db.models.fields.TimeField', [], {'default': 'datetime.time(23, 0)'}),
            'idealSleepTimeWeekend': ('django.db.models.fields.TimeField', [], {'default': 'datetime.time(0, 0)'}),
            'idealWakeupWeekday': ('django.db.models.fields.TimeField', [], {'default': 'datetime.time(8, 0)'}),
            'idealWakeupWeekend': ('django.db.models.fields.TimeField', [], {'default': 'datetime.time(9, 0)'}),
            'metrics': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['sleep.Metric']", 'symmetrical': 'False', 'blank': 'True'}),
            'mobile': ('django.db.models.fields.SmallIntegerField', [], {'default': '1'}),
            'moreMetrics': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'privacy': ('django.db.models.fields.SmallIntegerField', [], {'default': '0'}),
            'privacyFriends': ('django.db.models.fields.SmallIntegerField', [], {'default': '0'}),
            'privacyLoggedIn': ('django.db.models.fields.SmallIntegerField', [], {'default': '0'}),
            'punchInDelay': ('django.db.models.fields.DecimalField', [], {'default': '15', 'max_digits': '4', 'decimal_places': '2'}),
            'requested': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'requests'", 'blank': 'True', 'through': "orm['sleep.FriendRequest']", 'to': "orm['auth.User']"}),
            'timezone': ('django.db.models.fields.CharField', [], {'default': "'America/New_York'", 'max_length': '255'}),
            'use12HourTime': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'useGravatar': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['auth.User']", 'unique': 'True'})
        }
    }

    complete_apps = ['sleep']
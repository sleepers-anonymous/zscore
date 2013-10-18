from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import *
from django.utils.timezone import now
from django.core.cache import cache

from cache.decorators import cache_function
from cache.utils import authStatus, expireTemplateCache

class MetricsProfile(models.Model):
    user = models.OneToOneField(User)

    metrics = models.ManyToManyField('MetricsCategory', blank=True)

    #all other fields should have a default

class MetricsCategory(models.Model):
    METRIC_TYPE_BOOL = 0
    METRIC_TYPE_INT = 1

    METRIC_TYPE_CHOICES = (
            (METRIC_TYPE_BOOL, "boolean"),
            (METRIC_TYPE_INT, "int"),
        }
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    creator = models.ForeignKey(User, blank=True, null=True, editable = False) # is this a personal metric associated with a specific user, or a default metric for all users?

    metrictype = models.SmallIntegerField(choices = METRIC_TYPE_CHOICES, default=METRIC_TYPE_INT, editable=False)

    config = models.CharField(max_length = 255, null=True, blank=True)

class MetricsInstance(models.Model):
    time = models.DateTimeField()
    user = models.ForeignKey(User)
    category = models.ForeignKey(MetricsCategory)
    
    value = models.SmallIntegerField(blank=True, null=True)

    #all other fields should be nullable


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

    def __unicode__(self):
        return "Metrics Profile for " + str(self.user)

    def metricTypes(self):
        """Returns my metric types and also the default metric types"""
        return MetricsCategory.objects.filter(models.Q(creator=None) | models.Q(creator=self.user))

class MetricsCategory(models.Model):
    METRIC_TYPE_BOOL = 0
    METRIC_TYPE_INT = 1

    METRIC_TYPE_CHOICES = (
            (METRIC_TYPE_BOOL, "boolean"),
            (METRIC_TYPE_INT, "int"),
        )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    creator = models.ForeignKey(User, blank=True, null=True, editable = False, default=None) # is this a personal metric associated with a specific user, or a default metric for all users?

    metrictype = models.SmallIntegerField(choices = METRIC_TYPE_CHOICES, default=METRIC_TYPE_INT)

    minLabel = models.CharField(max_length = 255, null=True, blank=True)
    maxLabel = models.CharField(max_length = 255, null=True, blank=True)

    metricMax = models.SmallIntegerField(default=7)

    class Meta:
        unique_together = ('creator', 'name')

    def __unicode__(self):
        if self.creator:
            return self.name + " made by " + self.creator
        else:
            return self.name

class MetricsInstance(models.Model):
    time = models.DateTimeField()
    user = models.ForeignKey(User)

    values = models.ManyToManyField(MetricsCategory, through='SingleMetricsInstance')

    comments = models.TextField(blank=True, null=True)

    def __unicode__(self):
        return "MetricsInstance for " + str(self.user) + " at " + str(self.time)

class SingleMetricsInstance(models.Model):
    category = models.ForeignKey(MetricsCategory)
    instance = models.ForeignKey(MetricsInstance)

    value = models.SmallIntegerField(blank=True, null=True)

    comments = models.TextField(blank=True, null=True)

    def __unicode__(self):
        return "SingleMetricsInstance from " + str(self.instance) + ", " + str(self.category) + " (" + str(self.value) + ")"

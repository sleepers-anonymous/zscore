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
    PRIVACY_MIN = -100
    PRIVACY_HIDDEN = -100
    PRIVACY_NORMAL = 0
    PRIVACY_MAX = 0

    creator = models.ForeignKey(User, blank=True, null=True) # is this a personal metric associated with a specific user, or a default metric for all users? 

class MetricsInstance(models.Model):
    time = models.DateTimeField()
    user = models.ForeignKey(User)
    category = models.ForeignKey(MetricsCategory)
            
    #all other fields should be nullable



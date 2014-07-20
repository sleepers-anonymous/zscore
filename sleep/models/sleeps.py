#!/usr/bin/python

#For any models that have to do with basic sleep functionality

from django.db import IntegrityError
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import *
from django.utils.timezone import now
from django.core.mail import EmailMultiAlternatives
from django.core.cache import cache
from django.core.cache.utils import make_template_fragment_key
from django.db.models.signals import m2m_changed
from django.dispatch import receiver

import pytz
import datetime
import dateutil.parser
import math
import itertools
import hashlib
import random
import time
from operator import add
import numpy as np

from zscore import settings
from sleep import utils
from cache.decorators import cache_function
from cache.utils import authStatus, expireTemplateCache

TIMEZONES = zip(pytz.common_timezones, pytz.common_timezones)

class Metric(models.Model):
    name = models.CharField(max_length=40, unique=True)
    asHHMM, asInt = 'asHHMM', 'asInt'
    DISPLAY_STYLE_CHOICES = (
        (asHHMM, 'As HH:MM'),
        (asInt, 'As integer'))
    display_style = models.CharField(max_length = 6,
                                     choices = DISPLAY_STYLE_CHOICES,
                                     default = asHHMM)
    priority =  models.IntegerField(unique=True)
    # decides order in which metrics are displayed
    show_by_default = models.BooleanField(default=True)

    description = models.TextField(blank=True)
    short_description = models.TextField(blank=True)

    def __unicode__(self):
        return self.name

    def withAbbrDesc(self):
        if self.short_description:
            return '<abbr title="' + self.short_description + '">' + self.name + '</abbr>'
        else:
            return self.name

    class Meta:
        ordering = ['-priority']

class SleepManager(models.Manager):
    @cache_function(lambda self, user=None, group=None: () if user is None and group is None else None)
    def totalSleep(self, user=None,group=None):
        if user is None and group is None:
            sleeps = Sleep.objects.all()
        elif user is None:
            sleeps = Sleep.objects.filter(user__sleepergroups=group)
        elif group is None:
            sleeps = Sleep.objects.filter(user=user)
        else:
            raise ValueError, "Can't compute totalSleep with both a user and a group."
        return sum((sleep.end_time - sleep.start_time for sleep in sleeps),datetime.timedelta(0))

    def sleepTimes(self,res=1, user = None, group = None):
        if user is None and group is None:
            sleeps = Sleep.objects.all()
        elif user is None:
            sleeps = Sleep.objects.filter(user__sleepergroups=group)
        elif group is None:
            sleeps = Sleep.objects.filter(user=user)
        else:
            raise ValueError, "Can't compute sleepTimes with both a user and a group."
        atTime = [0] * (24 * 60 / res)
        for sleep in sleeps:
            tz = pytz.timezone(sleep.timezone)
            startLocal = sleep.start_local_time()
            endLocal = sleep.end_local_time()
            startDate = startLocal.date()
            endDate = endLocal.date()
            dr = [startDate + datetime.timedelta(i) for i in range((endDate-startDate).days + 1)]
            for d in dr:
                if d == startDate:
                    startTime = startLocal.time()
                else:
                    startTime = datetime.time(0)
                if d == endDate:
                    endTime = endLocal.time()
                else:
                    endTime = datetime.time(23,59)
                for i in range((startTime.hour * 60 + startTime.minute) / res, (endTime.hour * 60 + endTime.minute + 1) / res):
                    atTime[i]+=1
        return atTime

    def sleepStartEndTimes(self,res=10, user = None,group=None):
        if user is None and group is None:
            sleeps = Sleep.objects.all()
        elif user is None:
            sleeps = Sleep.objects.filter(user__sleepergroups=group)
        elif group is None:
            sleeps = Sleep.objects.filter(user=user)
        else:
            raise ValueError, "Can't compute sleepStartEndTimes with both a user and a group."
        startAtTime = [0] * (24 * 60 / res)
        endAtTime = [0] * (24 * 60 / res)
        for sleep in sleeps:
            tz = pytz.timezone(sleep.timezone)
            startTime = sleep.start_time.astimezone(tz).time()
            endTime = sleep.end_time.astimezone(tz).time()
            startAtTime[(startTime.hour * 60 + startTime.minute) / res]+=1
            endAtTime[(endTime.hour * 60 + endTime.minute) / res]+=1
        return (startAtTime,endAtTime)

    def sleepLengths(self,res=10, user = None,group=None):
        if user is None and group is None:
            sleeps = Sleep.objects.all()
        elif user is None:
            sleeps = Sleep.objects.filter(user__sleepergroups=group)
        elif group is None:
            sleeps = Sleep.objects.filter(user=user)
        else:
            raise ValueError, "Can't compute sleepStartEndTimes with both a user and a group."
        lengths = map(lambda x: x.length().total_seconds() / (60*res),sleeps)
        packed = [0] * int(max(lengths)+1)
        for length in lengths:
            if length>0:
                packed[int(length)]+=1
        return packed


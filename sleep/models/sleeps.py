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
        app_label = 'sleep'
        db_table = 'sleep_metric'

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

class PartialSleep(models.Model):
    user = models.OneToOneField(User)
    start_time = models.DateTimeField()
    timezone = models.CharField(max_length=255, choices = TIMEZONES, default=settings.TIME_ZONE)

    def __unicode__(self):
        tformat = "%I:%M %p %x" if self.user.sleeperprofile.use12HourTime else "%H:%M %x"
        return "Partial sleep beginning at %s" % self.start_local_time().strftime(tformat)

    def start_local_time(self):
        tz = pytz.timezone(self.timezone)
        return self.start_time.astimezone(tz)

    def gen_potential_wakeup(self):
        d = self.user.sleeperprofile.getPunchInDelay()
        s = self.start_local_time()
        return [s + d + (i*datetime.timedelta(hours=1.5)) for i in xrange(1,6)]

    @classmethod
    def create_new_for_user(cls, user):
        prof = user.sleeperprofile
        timezone = prof.timezone
        start = now().astimezone(pytz.timezone(timezone)).replace(microsecond=0) + prof.getPunchInDelay()
        try:
            p = PartialSleep(user=user, start_time=start, timezone=timezone)
            p.save()
            return True
        except IntegrityError:
            return False

    @classmethod
    def finish_for_user(cls, user):
        """Finish a user's partial sleep.

        Throws (partial list):
            - ValidationError
            - PartialSleep.DoesNotExist
        """
        timezone = user.sleeperprofile.timezone
        pytztimezone = pytz.timezone(timezone)
        p = user.partialsleep
        start = p.start_time.astimezone(pytztimezone)
        end = now().astimezone(pytz.timezone(timezone)).replace(microsecond = 0)
        date = end.date()
        s = Sleep(user=user,
            start_time=start, end_time=end, date=date, timezone=timezone,
            comments="",
            )
        s.validate_unique()
        s.save()
        p.delete()
        return s

class Sleep(models.Model):
    objects = SleepManager()

    user = models.ForeignKey(User)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    comments = models.TextField(blank=True)
    date = models.DateField()
    timezone = models.CharField(max_length=255, choices = TIMEZONES, default=settings.TIME_ZONE)
    sleepcycles = models.SmallIntegerField()

    quality = models.SmallIntegerField(choices=((0,"0 - awful"), (1,"1"),(2,"2"),(3,"3 - meh"),(4,"4"),(5,"5 - awesome")),default=4)

    active = models.BooleanField(default=True)

    def __unicode__(self):
        tformat = "%I:%M %p %x" if self.user.sleeperprofile.use12HourTime else "%H:%M %x"
        return "Sleep from %s to %s (%s)" % (self.start_local_time().strftime(tformat),self.end_local_time().strftime(tformat), self.getTZShortName())

    def length(self):
        return self.end_time - self.start_time

    def score(self, nightValue = 1.0):
        p = self.user.sleeperprofile
        length = self.length().total_seconds()
        tz = self.getSleepTZ()
        idealToday = p.getIdealSleepInterval(self.date, tz)
        idealYesterday = p.getIdealSleepInterval(self.date - datetime.timedelta(1), tz)
        idealTomorrow = p.getIdealSleepInterval(self.date + datetime.timedelta(1), tz)
        inIdeal = reduce(add, [utils.overlap((self.start_time, self.end_time), i) for i in [idealToday, idealYesterday, idealTomorrow]], datetime.timedelta(0)).total_seconds()
        score = nightValue*inIdeal + length - inIdeal
        return datetime.timedelta(seconds=score)

    def validate_unique(self, exclude=None):
        overlaps = Sleep.objects.filter(start_time__lt=self.end_time,end_time__gt=self.start_time,user=self.user)
        if self.pk is not None:
            overlaps = overlaps.exclude(pk = self.pk)
        if overlaps:
            raise ValidationError({NON_FIELD_ERRORS: ["This sleep overlaps with %s!" % overlaps[0]]})

    def start_local_time(self):
        tz = pytz.timezone(self.timezone)
        return self.start_time.astimezone(tz)

    def end_local_time(self):
        tz = pytz.timezone(self.timezone)
        return self.end_time.astimezone(tz)
    
    def getSleepTZ(self):
        """Returns the timezone as a timezone object"""
        return pytz.timezone(self.timezone)

    def updateTZ(self,tzname):
        """Updates the timezone while keeping the local time the same.  Intended for use from the shell; use at your own risk."""
        newtz = pytz.timezone(tzname)
        self.start_time = newtz.localize(self.start_local_time().replace(tzinfo=None))
        self.end_time = newtz.localize(self.end_local_time().replace(tzinfo=None))
        self.timezone = tzname #we have to make sure to do this last!
        self.save()

    def getTZShortName(self):
        """Gets the short of a time zone"""
        return self.end_local_time().tzname()

    def save(self, *args, **kwargs):
        seconds = self.length().total_seconds()
        self.sleepcycles = seconds//5400
        cache.delete('movingStats:%s' % self.user_id)
        cache.delete('decayStats:%s' % self.user_id)
        cache.delete('bestByTime:')
        cache.delete('sorted_sleepers:')
        cache.delete('totalSleep:')
        super(Sleep, self).save(*args,**kwargs)

    def delete(self, *args, **kwargs):
        cache.delete('movingStats:%s' % self.user_id)
        cache.delete('decayStats:%s' % self.user_id)
        cache.delete('bestByTime:')
        cache.delete('sorted_sleepers:')
        cache.delete('totalSleep:')
        super(Sleep, self).delete(*args,**kwargs)

class Allnighter(models.Model):
    user = models.ForeignKey(User)
    date = models.DateField()
    comments = models.TextField(blank=True)

    def validate_unique(self, exclude=None):
        try: user= self.user
        except:return None
        allnighterq = self.user.allnighter_set.filter(date=self.date).exclude(pk = self.pk)
        if allnighterq.count() != 0 :raise ValidationError({NON_FIELD_ERRORS: ["You have already entered an allnighter for %s" % self.date]})

    def __unicode__(self):
        return "All-nighter on " + self.date.strftime("%x")

    def delete(self, *args, **kwargs):
        cache.delete('decayStats:%s' % self.user_id)
        cache.delete('bestByTime:')
        cache.delete('sorted_sleepers:')
        super(Allnighter, self).delete(*args,**kwargs)

    def save(self, *args, **kwargs):
        cache.delete('decayStats:%s' % self.user_id)
        cache.delete('bestByTime:')
        cache.delete('sorted_sleepers:')
        super(Allnighter, self).save(*args,**kwargs)


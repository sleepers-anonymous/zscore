#!/usr/bin/python

#this file should contain anything that has to do with a sleeperprofile

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

class SchoolOrWorkPlace(models.Model):
    name = models.CharField(max_length=255)

    class Meta:
        app_label = "sleep"
        db_table = "sleep_schoolorworkplace"

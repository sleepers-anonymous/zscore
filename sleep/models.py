from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import *
from django.utils.timezone import now
from django.core.mail import EmailMultiAlternatives
from django.core.cache import cache
from django.db.models.signals import m2m_changed
from django.dispatch import receiver

import pytz
import datetime
import math
import itertools
import hashlib
import random
import time
from operator import add

from zscore import settings
from sleep import utils
from cache.decorators import cache_function
from cache.utils import authStatus, expireTemplateCache

TIMEZONES = [ (i,i) for i in pytz.common_timezones]

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
        d = user.sleeperprofile.getPunchInDelay()
        raise NotImplemented

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
        overlaps = Sleep.objects.filter(start_time__lt=self.end_time,end_time__gt=self.start_time,user=self.user).exclude(pk = self.pk)
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
        return self.getSleepTZ().tzname(datetime.datetime(self.date.year, self.date.month, self.date.day))

    def save(self, *args, **kwargs):
        seconds = self.length().total_seconds()
        self.sleepcycles = seconds//5400
        cache.delete('decayStats:%s' % self.user_id)
        cache.delete('bestByTime:')
        cache.delete('sorted_sleepers:')
        cache.delete('totalSleep:')
        super(Sleep, self).save(*args,**kwargs)

    def delete(self, *args, **kwargs):
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
        #Should edit to include the exclude field)
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

class SchoolOrWorkPlace(models.Model):
    name = models.CharField(max_length=255)

class SleeperProfile(models.Model):
    user = models.OneToOneField(User)
    # all other fields should have a default

    #--------------------------------------Privacy Settings -----------------------
    PRIVACY_HIDDEN = -100
    PRIVACY_REDACTED = -50
    PRIVACY_NORMAL = 0
    PRIVACY_STATS = 50
    PRIVACY_PUBLIC = 100
    PRIVACY_GRAPHS = 150
    PRIVACY_MAX = 200
    PRIVACY_CHOICES = (
            (PRIVACY_HIDDEN, 'Hidden'),
            (PRIVACY_REDACTED, 'Redacted'),
            (PRIVACY_NORMAL, 'Normal'),
            (PRIVACY_STATS, 'Stats Public'),
            (PRIVACY_PUBLIC, 'Sleep Public'),
            (PRIVACY_GRAPHS, 'Graphs Public'),
            (PRIVACY_MAX, 'Everything Public'),
            )
    privacy = models.SmallIntegerField(choices=PRIVACY_CHOICES,default=PRIVACY_NORMAL,verbose_name='Privacy to anonymous users')
    privacyLoggedIn = models.SmallIntegerField(choices=PRIVACY_CHOICES,default=PRIVACY_NORMAL,verbose_name='Privacy to logged-in users')
    privacyFriends = models.SmallIntegerField(choices=PRIVACY_CHOICES,default=PRIVACY_NORMAL,verbose_name='Privacy to friends')

    friends = models.ManyToManyField(User,related_name='friends+',blank=True)
    follows = models.ManyToManyField(User,related_name='follows+',blank=True)
    requested = models.ManyToManyField(User,related_name='requests',blank=True,through='FriendRequest')

    AUTO_ACCEPT_ALL = 100
    AUTO_ACCEPT_FRIENDS = 50
    AUTO_ACCEPT_NONE = 0
    AUTO_ACCEPT_CHOICES = (
            (AUTO_ACCEPT_ALL, 'Everyone'),
            (AUTO_ACCEPT_FRIENDS, 'Friends'),
            (AUTO_ACCEPT_NONE, 'No one'),
            )
    autoAcceptGroups = models.SmallIntegerField(choices=AUTO_ACCEPT_CHOICES, default=AUTO_ACCEPT_FRIENDS, verbose_name="People from whom you will automatically accept group invites.")
    
    use12HourTime = models.BooleanField(default=False)

    #----------------------------------------Mobile settings--------------------------
    FORCE_MOBILE = 2
    DETECT_MOBILE = 1
    FORCE_NONMOBILE = 0
    MOBILE_CHOICES = (
            (FORCE_NONMOBILE, "Force Nonmobile"),
            (DETECT_MOBILE, "Detect Mobile"),
            (FORCE_MOBILE, "Force Mobile"),
            )

    mobile = models.SmallIntegerField(choices=MOBILE_CHOICES, default=DETECT_MOBILE, verbose_name="Use mobile interface?")
    
    #---------------------------Related to emails ---------------------------
    emailreminders = models.BooleanField(default=False)
    emailSHA1 =  models.CharField(max_length=50, blank=True)
    emailSHA1GenerationDate = models.DateTimeField(default=now())
    emailActivated = models.BooleanField(default=False)
    emailTime = models.TimeField(default = datetime.time(12), verbose_name="Reminder email time")

    #---------------------------User customification -------------------------
    useGravatar = models.BooleanField(default=True)

    #---------------------------Timezones------------------------------------

    timezone = models.CharField(max_length=255, choices = TIMEZONES, default=settings.TIME_ZONE)

    punchInDelay = models.DecimalField(max_digits=4, decimal_places=2, default= 15, verbose_name="punch.in delay time, in minutes")

    #--------------------------Ideal Sleep Metrics--------------------------------

    idealSleep = models.DecimalField(max_digits=4, decimal_places=2, default = 7.5)
    #Decimalfield restricts to two decimal places, float would not.

    idealWakeupWeekend = models.TimeField(default = datetime.time(9))
    idealWakeupWeekday = models.TimeField(default = datetime.time(8))

    idealSleepTimeWeekend = models.TimeField(default = datetime.time(0))
    idealSleepTimeWeekday = models.TimeField(default = datetime.time(23))

    def save(self, *args, **kwargs):
        cache.delete('bestByTime:')
        cache.delete('sorted_sleepers:')
        cache.delete('getPermissions:')
        super(SleeperProfile, self).save(*args,**kwargs)

    def activateEmail(self, sha):
        """Activates the user's email address. Returns True on success and False on failure"""
        if now() - self.emailSHA1GenerationDate < datetime.timedelta(7): #if I generated this key less than a week ago....
            if sha == self.emailSHA1:
                self.emailActivated = True
                self.emailSHA1 = ''
                self.save()
                return True
        return False

    def genEmailSha(self, newemail = None, overrideTimeConstraint = False):
        """Generates a new email SHA and emails it to the user. Returns True on success and False on failure"""
        if not(overrideTimeConstraint) and (now() - self.emailSHA1GenerationDate < datetime.timedelta(hours=1)): return False
        user_hash = hashlib.sha1(self.user.username).hexdigest()[:10]
        random_salt = hashlib.sha1(str(random.random())).hexdigest()
        sha = hashlib.sha1(random_salt + user_hash).hexdigest()
        self.emailSHA1 = sha
        self.emailSHA1GenerationDate = now()
        self.emailActivated = False
        self.save()
        if newemail != None:
            self.user.email = newemail
            self.user.save()
        text = "<html> Hi " + self.user.username + "! <br /><br />"
        text += "Click on the following link in order to activate your email! <br /><br />"
        text += "<a href='http://zscore.xvm.mit.edu/accounts/emailconfirm/" + sha + "/'>http://zscore.xvm.mit.edu/accounts/emailconfirm/" + sha +"</a></html>"
        msg = EmailMultiAlternatives("zScore email activation", "", "zscore.noreply@gmail.com", [self.user.email])
        msg.attach_alternative(text, "text/html")
        msg.send()
        return True

    def getIdealSleep(self):
        """Returns idealSleep as a timedelta"""
        return datetime.timedelta(hours=float(self.idealSleep))

    def getFloatIdealSleep(self):
        """Retunes idealSleep as a float"""
        return float(self.idealSleep)

    def getPunchInDelay(self):
        """Return punchInDelay as a timedelta"""
        return datetime.timedelta(minutes=float(self.punchInDelay))

    def getUserTZ(self):
        """Returns user timezone as a timezone object"""
        return pytz.timezone(self.timezone)

    def today(self):
        """Returns a datetime.date object corresponding to the date the user thinks it is"""
        return now().astimezone(self.getUserTZ()).date()

    def getIdealSleepInterval(self, date, timezone=None):
        """Returns (idealSleepTime,idealWakeTime) for a user on a specific date, localized"""
        if timezone == None: timezone = self.getUserTZ()
        naiveIdeal = (self.idealSleepTimeWeekend, self.idealWakeupWeekend) if date.weekday() > 5 else (self.idealSleepTimeWeekday, self.idealWakeupWeekday)
        if naiveIdeal[0] > naiveIdeal[1]: #If my SleepTime "appears" to be greater than my Wakeup time....
            naiveIdeal = (datetime.datetime.combine(date-datetime.timedelta(1), naiveIdeal[0]), datetime.datetime.combine(date, naiveIdeal[1]))
        else:
            naiveIdeal = (datetime.datetime.combine(date, naiveIdeal[0]), datetime.datetime.combine(date, naiveIdeal[1]))
        localizedIdeal = (timezone.localize(naiveIdeal[0]), timezone.localize(naiveIdeal[1]))
        return localizedIdeal

    def isLikelyAsleep(self):
        today = self.today()
        today_interval = self.getIdealSleepInterval(today)
        n = now()
        if today_interval[0] <= n <= today_interval[1]: return True
        tomorrow_interval = self.getIdealSleepInterval(today + datetime.timedelta(1))
        if tomorrow_interval[0] <= n <= tomorrow_interval[1]: return True
        return False

    def isMobile(self, request):
        """Returns whether or not we should be assuming mobile or not"""
        if self.mobile == 2: return True
        if self.mobile == 0: return False

        #Mostly taken from https://github.com/gregmuellegger/django-mobile/blob/master/django_mobile/middleware.py
        #I didn't just use that code b/c I didn't want it to be middleware

        if request.META.has_key('HTTP_USER_AGENT'):
            userAgent = request.META["HTTP_USER_AGENT"]
            #Test for common mobile values first:
            if utils.userAgentsTestSearchRegex.search(userAgent) and not utils.userAgentsExceptionSearchRegex.search(userAgent): return True
            #Nokia is apparently a special snowflake, according to the folks who developed django-mobile
            if request.META.has_key('HTTP_ACCEPT'):
                httpAccept = request.META["HTTP_ACCEPT"]
                if utils.httpAcceptRegex.search(httpAccept): return True
            #Now test from the larger list
            if utils.userAgentsTestMatchRegex.match(userAgent): return True

        return False

    def getSimplePermissions(self, otherUser):
        """Returns the permissions an arbitrary user should have for me, ignoring groups and friends, and thus only differentiating between logged-in and anonymous users."""
        if otherUser.is_authenticated():
            return self.privacyLoggedIn
        else:
            return self.privacy

    @cache_function(lambda self, otherUser, otherUserGroupIDs=None: (self.id,otherUser.id),())
    def getPermissions(self, otherUser, otherUserGroupIDs=None):
        """Returns the permissions an other user should have for me.
        
        Pass either a user, or a string, like "friends", "user", "anon", if the user should be allowed to override.

        Use otherUserGroups iff you know what you're doing for efficiency.
        """
        otherD = {
                "friends": "privacyFriends",
                "user":"privacyLoggedIn",
                "anon": "privacy",
                }
        if otherUser in otherD: #we've passed one of the given strings; the code calling us should check that we're allowed to do this.
            return getattr(self, otherD[otherUser])
        elif otherUser == None or otherUser.is_anonymous():
            return self.privacy
        elif otherUser.id == self.user_id:
            return self.PRIVACY_MAX

        choices=[self.privacy,self.privacyLoggedIn]
        if otherUser in self.friends.all():
            choices.append(self.privacyFriends)
        #we really want to be able to filter the queryset, but it's probably prefetched, so don't.  (See Django #17001.)  I think this is probably the most efficient even though it's not ideal.
        myGs = list(self.user.membership_set.all())
        otherGIDs = otherUserGroupIDs if otherUserGroupIDs is not None else map(lambda x: x.id, otherUser.sleepergroups.all())
        bothGs = [m.privacy for m in myGs if m.group_id in otherGIDs]
        choices.extend(bothGs)
        return max(choices)

    def getEmailHash(self):
        if self.useGravatar:
            email = self.user.email.strip().lower()
            return hashlib.md5(email).hexdigest()
        else: return None

    def __unicode__(self):
        return "SleeperProfile for user %s" % self.user

@receiver(m2m_changed,sender=SleeperProfile.friends.through)
def expireGetPermissions(**kwargs):
    cache.delete('getPermissions:')

class SleeperManager(models.Manager):
    @cache_function(lambda self,sortBy='zScore',user=None,group=None: (sortBy,authStatus(user)) if group is None else None,())
    def sorted_sleepers(self,sortBy='zScore',user=None,group=None):
        if group is None:
            sleepers = Sleeper.objects.all()
            sleepers=sleepers.select_related('sleeperprofile','sleeperprofile__user').prefetch_related('sleep_set','allnighter_set')
        else:
            sleepers = Sleeper.objects.filter(sleepergroups=group)
            sleepers=sleepers.select_related('sleeperprofile','sleeperprofile__user').prefetch_related('sleep_set','allnighter_set','sleeperprofile__friends','sleeperprofile__user','sleeperprofile__user__membership_set')
            if 'is_authenticated' in dir(user) and user.is_authenticated():
                myGroupIDs = map(lambda x: x.id, user.sleepergroups.all())
            else:
                myGroupIDs=[]
        scored=[]
        extra=[]
        for sleeper in sleepers:
            if sleeper.sleep_set.count()>2 and sleeper.sleepPerDay(packDates=True)[-1]['date'] >= datetime.date.today()-datetime.timedelta(5):
                p = sleeper.sleeperprofile
                if user is 'all':
                    priv = p.PRIVACY_PUBLIC
                elif group is None:
                    priv = p.getSimplePermissions(user)
                else:
                    priv = p.getPermissions(user,otherUserGroupIDs=myGroupIDs)

                if priv<=p.PRIVACY_REDACTED:
                    sleeper.displayName="[redacted]"
                else:
                    sleeper.displayName=sleeper.username
                if priv>p.PRIVACY_HIDDEN:
                    d=sleeper.decayStats()
                    d['user']=sleeper
                    scored.append(d)
            else:
                d = sleeper.decayStats()
                d['rank']='n/a'
                sleeper.displayName=sleeper.username
                d['user']=sleeper
                extra.append(d)
        if sortBy in ['stDev', 'posStDev','idealDev']:
            scored.sort(key=lambda x: x[sortBy])
        else:
            scored.sort(key=lambda x: -x[sortBy])
        for i in xrange(len(scored)):
            scored[i]['rank']=i+1
        scored.extend(extra)
        return scored

    @cache_function(lambda self,start=datetime.datetime.min,end=datetime.datetime.max,user=None,group=None: (start.strftime('%Y-%m-%d-%H'),end.strftime('%Y-%m-%d-%H'),authStatus(user)) if group is None else None,())
    def bestByTime(self,start=datetime.datetime.min,end=datetime.datetime.max,user=None,group=None):
        if group is None:
            sleepers = Sleeper.objects.all()
            sleepers=sleepers.select_related('sleeperprofile','sleeperprofile__user').prefetch_related('sleep_set','allnighter_set')
        else:
            sleepers = Sleeper.objects.filter(sleepergroups=group)
            sleepers=sleepers.select_related('sleeperprofile','sleeperprofile__user').prefetch_related('sleep_set','allnighter_set','sleeperprofile__friends','sleeperprofile__user','sleeperprofile__user__membership_set')
            if 'is_authenticated' in dir(user) and user.is_authenticated():
                myGroupIDs = map(lambda x: x.id, user.sleepergroups.all())
            else:
                myGroupIDs=[]
        scored=[]
        for sleeper in sleepers:
            p = sleeper.sleeperprofile
            if user is 'all':
                priv = p.PRIVACY_PUBLIC
            elif group is None:
                priv = p.getSimplePermissions(user)
            else:
                priv = p.getPermissions(user,otherUserGroupIDs=myGroupIDs)

            if priv<=p.PRIVACY_REDACTED:
                sleeper.displayName="[redacted]"
            else:
                sleeper.displayName=sleeper.username
            if priv>p.PRIVACY_HIDDEN:
                d={'time':sleeper.timeSleptByTime(start,end,noFilter=True)}
                d['user']=sleeper
                scored.append(d)
        scored.sort(key=lambda x: -x['time'])
        for i in xrange(len(scored)): scored[i]['rank']=i+1
        return scored

class FriendRequest(models.Model):
    requestor = models.ForeignKey(SleeperProfile)
    requestee = models.ForeignKey(User)
    accepted = models.NullBooleanField()

    def save(self,*args,**kwargs):
        expireTemplateCache('header',self.requestee.username)
        super(FriendRequest,self).save(*args,**kwargs)
        

class Sleeper(User):
    class Meta:
        proxy = True

    objects = SleeperManager()

    def getOrCreateProfile(self):
        print "You probably don't actually want this method, User.sleeperprofile should work just fine."
        return SleeperProfile.objects.get_or_create(user=self)[0]

    def timeSleptByDate(self,start=datetime.date.min,end=datetime.date.max):
        sleeps = self.sleep_set.filter(date__gte=start,date__lte=end)
        return sum([s.end_time-s.start_time for s in sleeps],datetime.timedelta(0))

    def timeSleptByTime(self,start=datetime.datetime.min,end=datetime.datetime.max,noFilter=False):
        '''Use noFilter if you want to prefetch stuff.  If in doubt, leave it False.'''
        if noFilter:
            sleeps = self.sleep_set.all()
            return sum([min(s.end_time,end)-max(s.start_time,start) for s in sleeps if s.end_time>=start and s.start_time<=end],datetime.timedelta(0))
        else:
            sleeps = self.sleep_set.filter(end_time__gt=start,start_time__lt=end)
            return sum([min(s.end_time,end)-max(s.start_time,start) for s in sleeps],datetime.timedelta(0))

    def sleepPerDay(self,start=datetime.date.min,end=datetime.date.max,packDates=False,hours=False,includeMissing=False):
        if start==datetime.date.min and end==datetime.date.max:
            sleeps = self.sleep_set.all()
            allnighters = self.allnighter_set.all()
        else:
            sleeps = self.sleep_set.filter(date__gte=start,date__lte=end)
            allnighters = self.allnighter_set.filter(date__gte=start,date__lte=end)
        if sleeps:
            allnighters=[x.date for x in iter(allnighters)] #map(lambda x: x.date,allnighters)
            sleeps=list(iter(sleeps))
            dates=[x.date for x in sleeps] #map(lambda x: x.date, sleeps)
            first = min(itertools.chain(dates,allnighters))
            last = max(itertools.chain(dates,allnighters))
            n = (last-first).days + 1
            dateRange = [first + datetime.timedelta(i) for i in range(0,n)]
            byDays = [sum([s.length().total_seconds() for s in sleeps if s.date==d]) for d in dateRange]
            if hours:
                byDays = map(lambda x: x/3600,byDays)
            if packDates:
                return [{'date' : first + datetime.timedelta(i), 'slept' : byDays[i]} for i in range(0,n) if byDays[i]>0 or first + datetime.timedelta(i) in allnighters or includeMissing]
            else:
                return [byDays[i] for i in range(0,n) if byDays[i]>0 or first+datetime.timedelta(i) in allnighters or includeMissing]
        else:
            return []

    def genDays(start,end):
        d=start
        while d <= end:
            yield d
            d += datetime.timedelta(1)

    def sleepWakeTime(self,t='end',start=datetime.date.today(),end=datetime.date.today(), stdev = False):
        sleeps = self.sleep_set.filter(date__gte=start,date__lte=end)
        if t=='end':
            f=Sleep.end_local_time
            g = min
        elif t=='start':
            f=Sleep.start_local_time
            g = max
        else: return None
        datestimes = [(s.date, f(s)) for s in sleeps if s.length() >= datetime.timedelta(hours=3)]
        daily={}
        for i in datestimes:
            if i[0] in daily: daily[i[0]]=g(daily[i[0]],i[1])
            else: daily[i[0]]=i[1]
        seconds = [daily[t].time().hour*3600 + daily[t].time().minute*60 + daily[t].time().second - 86400 * (t - daily[t].date()).days for t in daily.viewkeys()]
        if daily:
            av = 1.0*sum(seconds)/len(seconds)
            if stdev:
                if len(daily) > 2: stdev = (sum([(av - s)**2 for s in seconds])/(len(seconds)-1.5))**0.5
                else: stdev = False
            av = av%86400
            sleepav =  datetime.time(int(math.floor(av/3600)), int(math.floor((av%3600)/60)), int(math.floor((av%60))))
            return (sleepav, datetime.timedelta(seconds=stdev)) if stdev else sleepav
        else:
            return None

    def goToSleepTime(self, date=datetime.date.today(), stdev = False):
        return self.sleepWakeTime('start',date,date, stdev=stdev)

    def avgGoToSleepTime(self, start = datetime.date.min, end=datetime.date.max, stdev = False):
        return self.sleepWakeTime('start',start,end, stdev = stdev)

    def wakeUpTime(self, date=datetime.date.today(), stdev = False):
        return self.sleepWakeTime('end',date,date, stdev = stdev)

    def avgWakeUpTime(self, start = datetime.date.min, end=datetime.date.max, stdev = False):
        return self.sleepWakeTime('end',start,end, stdev = stdev)

    @cache_function(lambda self,start=datetime.date.min,end=datetime.date.max: (self.id,start,end), lambda self,start=datetime.date.min,end=datetime.datetime.max: (self.id,))
    def movingStats(self,start=datetime.date.min,end=datetime.date.max):
        sleep = self.sleepPerDay(start,end)
        ideal = int(self.sleeperprofile.getFloatIdealSleep()*3600)
        d = {}
        try:
            avg = sum(sleep)/len(sleep)
            d['avg']=avg
            if len(sleep)>2:
                stDev = math.sqrt(sum(map(lambda x: (x-avg)**2, sleep))/(len(sleep)-1.5)) #subtracting 1.5 is correct according to wikipedia
                posStDev = math.sqrt(sum(map(lambda x: min(0,x-avg)**2, sleep))/(len(sleep)-1.5)) #subtracting 1.5 is correct according to wikipedia
                d['stDev']=stDev
                d['posStDev']=posStDev
                d['zScore']=avg-stDev
                d['zPScore']=avg-posStDev
                idealized = max(ideal, avg)
                d['idealDev'] = math.sqrt(sum(map(lambda x: (x-idealized)**2, sleep))/(len(sleep)-1.5))
                d['consistent'] = self.consistencyStat(start = start, end = end)
                d['consistent2'] = self.consistencyStat2(start = start, end = end)
        except:
            pass
        try:
            offset = 60*60.
            avgRecip = 1/(sum(map(lambda x: 1/(offset+x),sleep))/len(sleep))-offset
            d['avgRecip']=avgRecip
            avgSqrt = (sum(map(lambda x: math.sqrt(x),sleep))/len(sleep))**2
            d['avgSqrt']=avgSqrt
            avgLog = math.exp(sum(map(lambda x: math.log(x+offset),sleep))/len(sleep))-offset
            d['avgLog']=avgLog
        except:
            pass
        for k in ['avg','posStDev','zPScore','stDev','zScore','avgSqrt','avgLog','avgRecip', 'idealDev']:
            if k not in d:
                d[k]=datetime.timedelta(0)
            else:
                d[k]=datetime.timedelta(0,d[k])
        return d

    def consistencyStat(self,res=1, start = datetime.date.min, end = datetime.date.max, decay = False, hl = 4):
        sleeps = self.sleep_set.all()
        atTime = [0] * (24 * 60 / res)
        sleepdates = set([sleep.date for sleep in sleeps if sleep.date >= start and sleep.date <= end])
        if len(sleepdates) < 2:
            return 0
        maxdate = max(sleepdates)
        if len([day for day in sleepdates if (maxdate-day).days < 14]) < 3:
            return 0
        for sleep in sleeps:
            if sleep.date <= end and sleep.date >= start:
                startDate = sleep.start_local_time().date()
                endDate = sleep.end_local_time().date()
                dr = [startDate + datetime.timedelta(i) for i in range((endDate-startDate).days + 1)]
                for d in dr:
                    if d == startDate:
                        startTime = sleep.start_local_time().time()
                    else:
                        startTime = datetime.time(0)
                    if d == endDate:
                        endTime = sleep.end_local_time().time()
                    else:
                        endTime = datetime.time(23,59)
                    for i in range((startTime.hour * 60 + startTime.minute) / res, (endTime.hour * 60 + endTime.minute + 1) / res):
                        if decay:
                            atTime[i] += 2**(-(maxdate-sleep.date).days/float(hl))
                        else:
                            atTime[i]+=1
        numerator = sum(map(lambda x: x**2, atTime))
        if decay:
            numDays = sum([2**(-((maxdate-day).days/float(hl))) for day in sleepdates])
        else:
            numDays = len(sleepdates)
        denominator = sum(atTime) * numDays
        try:
            if int(1000 * float(numerator)/denominator) <= 1000:
                return int(1000 * float(numerator)/denominator)
            else:
                return 0
        except:
            return 0

    def consistencyStat2(self,res=1, start = datetime.date.min, end = datetime.date.max, decay = False, hl = 4):
        sleeps = self.sleep_set.all()
        atTime = [0] * (24 * 60 / res)
        sleepdates = set([sleep.date for sleep in sleeps if sleep.date >= start and sleep.date <= end])
        if len(sleepdates) < 2:
            return 0
        maxdate = max(sleepdates)
        if len([day for day in sleepdates if (maxdate-day).days < 14]) < 3:
            return 0
        for sleep in sleeps:
            if sleep.date <= end and sleep.date >= start:
                startDate = sleep.start_local_time().date()
                endDate = sleep.end_local_time().date()
                dr = [startDate + datetime.timedelta(i) for i in range((endDate-startDate).days + 1)]
                for d in dr:
                    if d == startDate:
                        startTime = sleep.start_local_time().time()
                    else:
                        startTime = datetime.time(0)
                    if d == endDate:
                        endTime = sleep.end_local_time().time()
                    else:
                        endTime = datetime.time(23,59)
                    for i in range((startTime.hour * 60 + startTime.minute) / res, (endTime.hour * 60 + endTime.minute + 1) / res):
                        if decay:
                            atTime[i] += 2**(-(maxdate-sleep.date).days/float(hl))
                        else:
                            atTime[i]+=1
        if decay:
            numDays = sum([2**(-((maxdate-day).days/float(hl))) for day in sleepdates])
        else:
            numDays = len(sleepdates)
        return int(1000 * sum([(float(i)/numDays) ** 2 + (1-float(i)/numDays) ** 2 for i in atTime]) / (24 * 60))
        
        
    def decaying(self,data,hl,stDev=False):
        s = 0
        w = 0
        for i in range(len(data)):
            s+=2**(-i/float(hl))*data[-i-1]
            w+=2**(-i/float(hl))
        if stDev:
            w = w*(len(data)-1.5)/len(data)
        return s/w

    @cache_function(lambda self,end=datetime.date.max,hl=4: (self.id,end,hl), lambda self,end=datetime.date.max,hl=4: (self.id,))
    def decayStats(self,end=datetime.date.max,hl=4):
        sleep = self.sleepPerDay(datetime.date.min,end)
        ideal = int(self.sleeperprofile.getFloatIdealSleep()*3600)
        d = {}
        try:
            avg = self.decaying(sleep,hl)
            d['avg']=avg
            stDev = math.sqrt(self.decaying(map(lambda x: (x-avg)**2,sleep),hl,True))
            posStDev = math.sqrt(self.decaying(map(lambda x: min(0,x-avg)**2,sleep),hl,True))
            d['stDev']=stDev
            d['posStDev']=posStDev
            d['zScore']=avg-stDev
            d['zPScore']=avg-posStDev
            idealized = max(ideal, avg)
            d['idealDev']=math.sqrt(self.decaying(map(lambda x: (x - idealized)**2 , sleep),hl, True))
            d['consistent'] = self.consistencyStat(end = end, decay = True, hl = hl)
            d['consistent2'] = self.consistencyStat2(end = end, decay = True, hl = hl)
        except:
            pass
        try:
            offset = 60*60.
            avgRecip = 1/(self.decaying(map(lambda x: 1/(offset+x),sleep),hl))-offset
            d['avgRecip']=avgRecip
            avgSqrt = self.decaying(map(lambda x: math.sqrt(x),sleep),hl)**2
            d['avgSqrt']=avgSqrt
            avgLog = math.exp(self.decaying(map(lambda x: math.log(x+offset),sleep),hl))-offset
            d['avgLog']=avgLog
        except:
            pass
        for k in ['avg','posStDev','zPScore','stDev','zScore','avgSqrt','avgLog','avgRecip', 'idealDev']:
            if k not in d:
                d[k]=datetime.timedelta(0)
            else:
                d[k]=datetime.timedelta(0,d[k])
        return d

class SleeperGroup(models.Model):
    name = models.CharField(max_length=255, unique=True)
    members = models.ManyToManyField(User,related_name='sleepergroups',blank=True,through='Membership')
    defunctMembers = models.ManyToManyField(User, related_name='defunct+', blank=True)
    description = models.TextField(blank=True)

    PUBLIC = 100
    REQUEST = 50
    CLOSED = 0
    PRIVACY_OPTIONS = (
            (PUBLIC,"public"),
            (REQUEST,"request-only"),
            (CLOSED,"closed"),
            )
            
    privacy = models.SmallIntegerField(choices=PRIVACY_OPTIONS, default=REQUEST, verbose_name="Group privacy setting")

    def __unicode__(self):
        return "SleeperGroup %s" % self.name

    def invite(self,sleeper,inviter):
        if self.members.filter(id=sleeper.id).exists(): #if they're a member of the group
            return
        if GroupInvite.objects.filter(user=sleeper,group=self,accepted=None).exists(): # if they're already invited
            return
        autoAccept = sleeper.sleeperprofile.autoAcceptGroups
        i=GroupInvite(user=sleeper,group=self,accepted=None)
        i.save()
        if (autoAccept >= SleeperProfile.AUTO_ACCEPT_ALL or autoAccept >= SleeperProfile.AUTO_ACCEPT_FRIENDS and sleeper.sleeperprofile.friends.filter(id=inviter.id).exists()) and not GroupInvite.objects.filter(user=sleeper,group=self,accepted=False): # if they will auto-accept the request
            i.accept()

    def request(self, sleeper):
        if self.members.filter(id=sleeper.id).exists(): #if they're already a member of the group
            raise ValueError, "Already member of group " +  self.name
        if GroupRequest.objects.filter(user=sleeper, group=self).exists(): # if they've made a request in the past
            return
        i = GroupRequest(user=sleeper, group=self, accepted=None)
        i.save()

    def delete(self, *args, **kwargs):
        """Override the delete function in order to remove all membership objects associated with a group first."""
        for m in tuple(self.membership_set.all()):
            m.delete()
        super(SleeperGroup, self).delete(args, **kwargs)

class Membership(models.Model):
    user=models.ForeignKey(User)
    group=models.ForeignKey(SleeperGroup)
    privacy=models.SmallIntegerField(choices=SleeperProfile.PRIVACY_CHOICES,default=SleeperProfile.PRIVACY_NORMAL,verbose_name='Privacy to members of the given group')

    MEMBER = 0
    ADMIN = 50

    ROLE_CHOICES = (
            (MEMBER, "member"),
            (ADMIN, "administrator"),
            )

    role = models.SmallIntegerField(choices=ROLE_CHOICES,default=MEMBER)

    def __unicode__(self):
        return "%s is a(n) %s of %s" % (self.user,self.get_role_display(),self.group)

    def makeAdmin(self):
        self.role = 50
        self.save()

    def makeMember(self):
        otherAdmins = self.group.membership_set.filter(role__gte=50).count()
        if otherAdmins >= 2:
            self.role = 0
            self.save()
        else:
            raise ValueError, "Cannot remove last admin of a group"

    def removeMember(self):
        otherMembers = self.group.membership_set.all().count()
        if otherMembers >= 2:
            if self.role >= 50: self.makeMember() # attempt to make self not an admin if am admin
            self.delete()
        else:
            self.group.delete()
            return "redirect"

    def delete(self,*args,**kwargs):
        cache.delete("getPermissions:")
        super(Membership,self).delete(*args,**kwargs)

    def save(self,*args,**kwargs):
        cache.delete("getPermissions:")
        super(Membership,self).save(*args,**kwargs)

class GroupInvite(models.Model):
    user=models.ForeignKey(User)
    group=models.ForeignKey(SleeperGroup)
    accepted=models.NullBooleanField()

    def __unicode__(self):
        return "%s was invited to %s" % (self.user, self.group)

    def accept(self,privacy=None):
        if privacy is None:
            privacy=self.user.sleeperprofile.privacyLoggedIn
        m=Membership(user=self.user,group=self.group,privacy=privacy)
        m.save()
        self.accepted=True
        self.save()
    
    def reject(self):
        self.accepted=False
        self.save()

    def save(self,*args,**kwargs):
        expireTemplateCache('header',self.user.username)
        super(GroupInvite,self).save(*args,**kwargs)

class GroupRequest(models.Model):
    user = models.ForeignKey(User)
    group = models.ForeignKey(SleeperGroup)
    accepted = models.NullBooleanField()

    def __unicode__(self):
        return "%s requests admission to %s" % (self.user, self.group)

    def accept(self, privacy = None):
        if privacy is None:
            privacy = self.user.sleeperprofile.privacyLoggedIn
        m = Membership(user=self.user, group=self.group, privacy=privacy)
        m.save()
        self.accepted = True
        self.save()

    def reject(self):
        self.accepted=False
        self.save()

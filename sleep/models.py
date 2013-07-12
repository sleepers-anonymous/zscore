from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import *

import pytz
import datetime
import math
import itertools
import hashlib

from zscore import settings

TIMEZONES = [ (i,i) for i in pytz.common_timezones]

class SleepManager(models.Manager):
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
            startDate = sleep.start_time.astimezone(tz).date()
            endDate = sleep.end_time.astimezone(tz).date()
            dr = [startDate + datetime.timedelta(i) for i in range((endDate-startDate).days + 1)]
            for d in dr:
                if d == startDate:
                    startTime = sleep.start_time.astimezone(tz).time()
                else:
                    startTime = datetime.time(0)
                if d == endDate:
                    endTime = sleep.end_time.astimezone(tz).time()
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

class Sleep(models.Model):
    objects = SleepManager()

    user = models.ForeignKey(User)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    comments = models.TextField(blank=True)
    date = models.DateField()
    timezone = models.CharField(max_length=255, choices = TIMEZONES, default=settings.TIME_ZONE)
    sleepcycles = models.SmallIntegerField()

    def __unicode__(self):
        tformat = "%I:%M %p %x" if self.user.sleeperprofile.use12HourTime else "%H:%M %x"
        return "Sleep from %s to %s (%s)" % (self.start_local_time().strftime(tformat),self.end_local_time().strftime(tformat), self.getTZShortName())

    def length(self):
        return self.end_time - self.start_time

    def score(self, nightValue = 1.0):
        p = self.user.sleeperprofile
        pass

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

    def save(self, **kwargs):
        seconds = self.length().total_seconds()
        self.sleepcycles = seconds//5400
        super(Sleep, self).save(**kwargs)

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

class SchoolOrWorkPlace(models.Model):
    name = models.CharField(max_length=255)

class SleeperProfile(models.Model):
    user = models.OneToOneField(User)
    # all other fields should have a default
    PRIVACY_HIDDEN = -100
    PRIVACY_REDACTED = -50
    PRIVACY_NORMAL = 0
    PRIVACY_STATS = 50
    PRIVACY_PUBLIC = 100
    PRIVACY_GRAPHS = 150
    PRIVACY_MAX = 150
    PRIVACY_CHOICES = (
            (PRIVACY_HIDDEN, 'Hidden'),
            (PRIVACY_REDACTED, 'Redacted'),
            (PRIVACY_NORMAL, 'Normal'),
            (PRIVACY_STATS, 'Stats Public'),
            (PRIVACY_PUBLIC, 'Sleep Public'),
            (PRIVACY_GRAPHS, 'Graphs Public'),
            )
    privacy = models.SmallIntegerField(choices=PRIVACY_CHOICES,default=PRIVACY_NORMAL,verbose_name='Privacy to anonymous users')
    privacyLoggedIn = models.SmallIntegerField(choices=PRIVACY_CHOICES,default=PRIVACY_NORMAL,verbose_name='Privacy to logged-in users')
    privacyFriends = models.SmallIntegerField(choices=PRIVACY_CHOICES,default=PRIVACY_NORMAL,verbose_name='Privacy to friends')
    friends = models.ManyToManyField(User,related_name='friends+',blank=True)
    follows = models.ManyToManyField(User,related_name='follows+',blank=True)
    requested = models.ManyToManyField(User,related_name='requests',blank=True,through='FriendRequest')
    use12HourTime = models.BooleanField(default=False)

    emailreminders = models.BooleanField(default=False)
    useGravatar = models.BooleanField(default=True)

    timezone = models.CharField(max_length=255, choices = TIMEZONES, default=settings.TIME_ZONE)

    idealSleep = models.DecimalField(max_digits=4, decimal_places=2, default = 7.5)
    #Decimalfield restricts to two decimal places, float would not.

    idealWakeupWeekend = models.TimeField(default = datetime.time(9))
    idealWakeupWeekday = models.TimeField(default = datetime.time(8))

    idealSleepTimeWeekend = models.TimeField(default = datetime.time(0))
    idealSleepTimeWeekday = models.TimeField(default = datetime.time(23))

    def getIdealSleep(self):
        """Returns idealSleep as a timedelta"""
        return datetime.timedelta(hours=float(self.idealSleep))

    def getFloatIdealSleep(self):
        """Rtunes idealSleep as a float"""
        return float(self.idealSleep)

    def getUserTZ(self):
        """Returns user timezone as a timezone object"""
        return pytz.timezone(self.timezone)

    def getPermissions(self, otherUser):
        """Returns the permissions an other user should have for me.
        
        Pass either a user, or a string, like "friends", "user", "anon", if the user should be allowed to override.
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
        elif otherUser.pk == self.user.pk:
            return self.PRIVACY_MAX

        choices=[self.privacy,self.privacyLoggedIn]
        if otherUser in self.friends.all():
            choices.append(self.privacyFriends)
        #we really want to be able to filter the queryset, but it's probably prefetched, so don't.  (See Django #17001.)  I think this is probably the most efficient even though it's not ideal.
        myGs = list(self.user.membership_set.all())
        otherGIDs = map(lambda x: x.id, otherUser.sleepergroups.all())
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

class SleeperManager(models.Manager):
    def sorted_sleepers(self,sortBy='zScore',user=None,group=None):
        if group is None:
            sleepers = Sleeper.objects.all()
        else:
            sleepers = Sleeper.objects.filter(sleepergroups=group)
        sleepers=sleepers.prefetch_related('sleep_set','sleeperprofile','allnighter_set')
        scored=[]
        extra=[]
        for sleeper in sleepers:
            if len(sleeper.sleepPerDay())>2 and sleeper.sleepPerDay(packDates=True)[-1]['date'] >= datetime.date.today()-datetime.timedelta(5):
                p = sleeper.sleeperprofile
                if user is 'all': priv = p.PRIVACY_PUBLIC
                else: priv = p.getPermissions(user)

                if priv<=p.PRIVACY_REDACTED: sleeper.displayName="[redacted]"
                else: sleeper.displayName=sleeper.username
                if priv>p.PRIVACY_HIDDEN:
                    d=sleeper.decayStats()
                    d['user']=sleeper
                    if 'is_authenticated' in dir(user) and user.is_authenticated():
                        if user.pk==sleeper.pk: d['opcode']='me' #I'm using opcodes to mark specific users as self or friend.
                    else: d['opcode'] = None
                    scored.append(d)
            else:
                if 'is_authenticated' in dir(user) and user.is_authenticated() and user.pk == sleeper.pk:
                    d = sleeper.decayStats()
                    d['rank']='n/a'
                    sleeper.displayName=sleeper.username
                    d['user']=sleeper
                    d['opcode']='me'
                    extra.append(d)
        if sortBy in ['stDev', 'posStDev','idealDev']:
            scored.sort(key=lambda x: x[sortBy])
        else:
            scored.sort(key=lambda x: -x[sortBy])
        for i in xrange(len(scored)):
            scored[i]['rank']=i+1
        return scored+extra

    def bestByTime(self,start=datetime.datetime.min,end=datetime.datetime.max,user=None,group=None):
        if group is None:
            sleepers = Sleeper.objects.all()
        else:
            sleepers = Sleeper.objects.filter(sleepergroups=group)
        sleepers=sleepers.prefetch_related('sleep_set','sleeperprofile','allnighter_set')
        scored=[]
        for sleeper in sleepers:
            p = sleeper.sleeperprofile
            if user is 'all': priv = p.PRIVACY_PUBLIC
            else: priv = p.getPermissions(user)

            if priv<=p.PRIVACY_REDACTED: sleeper.displayName="[redacted]"
            else: sleeper.displayName=sleeper.username
            if priv>p.PRIVACY_HIDDEN:
                d={'time':sleeper.timeSleptByTime(start,end)}
                d['user']=sleeper
                if 'is_authenticated' in dir(user) and user.is_authenticated():
                    if user.pk==sleeper.pk: d['opcode']='me' #I'm using opcodes to mark specific users as self or friend.
                else: d['opcode'] = None
                scored.append(d)
        scored.sort(key=lambda x: -x['time'])
        for i in xrange(len(scored)): scored[i]['rank']=i+1
        return scored

class FriendRequest(models.Model):
    requestor = models.ForeignKey(SleeperProfile)
    requestee = models.ForeignKey(User)
    accepted = models.NullBooleanField()
        

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

    def timeSleptByTime(self,start=datetime.datetime.min,end=datetime.datetime.max):
        sleeps = self.sleep_set.filter(end_time__gt=start,start_time__lt=end)
        return sum([min(s.end_time,end)-max(s.start_time,start) for s in sleeps],datetime.timedelta(0))

    def sleepPerDay(self,start=datetime.date.min,end=datetime.date.max,packDates=False,hours=False):
        if start==datetime.date.min and end==datetime.date.max:
            sleeps = self.sleep_set.all()
            allnighters = self.allnighter_set.all()
        else:
            sleeps = self.sleep_set.filter(date__gte=start,date__lte=end)
            allnighters = self.allnighter_set.filter(date__gte=start,date__lte=end)
        if sleeps:
            allnighters=map(lambda x: x.date,allnighters)
            dates=map(lambda x: x.date, sleeps)
            first = min(itertools.chain(dates,allnighters))
            last = max(itertools.chain(dates,allnighters))
            n = (last-first).days + 1
            dateRange = [first + datetime.timedelta(i) for i in range(0,n)]
            byDays = [sum([s.length().total_seconds() for s in filter(lambda x: x.date==d,sleeps)]) for d in dateRange]
            if hours:
                byDays = map(lambda x: x/3600,byDays)
            if packDates:
                return [{'date' : first + datetime.timedelta(i), 'slept' : byDays[i]} for i in range(0,n) if byDays[i]>0 or first + datetime.timedelta(i) in allnighters]
            else:
                return [byDays[i] for i in range(0,n) if byDays[i]>0 or first+datetime.timedelta(i) in allnighters]
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

    def decaying(self,data,hl,stDev=False):
        s = 0
        w = 0
        for i in range(len(data)):
            s+=2**(-i/float(hl))*data[-i-1]
            w+=2**(-i/float(hl))
        if stDev:
            w = w*(len(data)-1.5)/len(data)
        return s/w

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

    def __unicode__(self):
        return "SleeperGroup %s" % self.name

class Membership(models.Model):
    user=models.ForeignKey(User)
    group=models.ForeignKey(SleeperGroup)
    privacy=models.SmallIntegerField(choices=SleeperProfile.PRIVACY_CHOICES,default=SleeperProfile.PRIVACY_NORMAL,verbose_name='Privacy to members of the given group')

    def __unicode__(self):
        return "%s is a member of %s" % (self.user,self.group)

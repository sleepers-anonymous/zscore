from django.db import models
from django.contrib.auth.models import User

import datetime
import math

class SleepManager(models.Manager):
    def totalSleep(self):
        sleeps =  Sleep.objects.all()
        return sum((sleep.end_time - sleep.start_time for sleep in sleeps),datetime.timedelta(0))

class Sleep(models.Model):
    objects = SleepManager()

    user = models.ForeignKey(User)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    comments = models.TextField(blank=True)
    date = models.DateField()

    def __unicode__(self):
        return "Sleep from %s to %s" % (self.start_time,self.end_time)

class SleeperManager(models.Manager):
    def sorted_sleepers(self):
        sleepers = Sleeper.objects.all().prefetch_related('sleep_set')
        scored=[]
        for sleeper in sleepers:
            d=sleeper.movingStats()
            d['user']=sleeper
            scored.append(d)
        scored.sort(key=lambda x: -x['zScore'])
        for i in xrange(len(scored)):
            scored[i]['rank']=i+1
        return scored
        




class Sleeper(User):
    class Meta:
        proxy = True

    objects = SleeperManager()

    def timeSlept(self,d):
        sleeps = self.sleep_set.filter(date=d)
        return sum([s.end_time-s.start_time for s in sleeps],datetime.timedelta(0))

    def sleepPerDay(self,start=datetime.date.min,end=datetime.date.max,packDates=False,hours=False):
        sleeps = self.sleep_set.filter(date__gte=start,date__lte=end).values('date','start_time','end_time')
        if sleeps:
            dates=map(lambda x: x['date'], sleeps)
            first = min(dates)
            last = max(dates)
            n = (last-first).days + 1
            dateRange = [first + datetime.timedelta(i) for i in range(0,n)]
            byDays = [sum([(s['end_time']-s['start_time']).total_seconds() for s in filter(lambda x: x['date']==d,sleeps)]) for d in dateRange]
            if hours:
                byDays = map(lambda x: x/3600,byDays)
            if packDates:
                return [{'date' : first + datetime.timedelta(i), 'slept' : byDays[i]} for i in range(0,n)]
            else:
                return byDays
        else:
            return []

    def movingStats(self,start=datetime.date.min,end=datetime.date.max):
        sleep = self.sleepPerDay(start,end)
        if sleep:
            avg = sum(sleep)/len(sleep)
            stDev = math.sqrt(sum(map(lambda x: (x-avg)**2, sleep))/len(sleep))
            avgSqrt = sum(map(lambda x: math.sqrt(3600*8*x),sleep))/len(sleep)
            d = {
                    'avg' : datetime.timedelta(0,avg),
                    'stDev' : datetime.timedelta(0,stDev),
                    'zScore' : datetime.timedelta(0,avg-stDev),
                    'avgSqrt' : datetime.timedelta(0,avgSqrt),
                    }
        else:
            d = {
                    'avg' : datetime.timedelta(0),
                    'stDev' : datetime.timedelta(0),
                    'zScore' : datetime.timedelta(0),
                    'avgSqrt' : datetime.timedelta(0),
                    }
        return d

    def decaying(self,data,hl):
        s = 0
        w = 0
        for i in range(len(data)):
            s+=2**(-i/float(hl))*data[-i-1]
            w+=2**(-i/float(hl))
        return s/w

    def decayStats(self,end=datetime.date.max,hl=3):
        sleep = self.sleepPerDay(datetime.date.min,end)
        if sleep:
            avg = self.decaying(sleep,hl)
            stDev = math.sqrt(self.decaying(map(lambda x: (x-avg)**2,sleep),hl))
            avgSqrt = self.decaying(map(lambda x: math.sqrt(3600*8*x),sleep),hl)
            d = {
                    'avg' : datetime.timedelta(0,avg),
                    'stDev' : datetime.timedelta(0,stDev),
                    'zScore' : datetime.timedelta(0,avg-stDev),
                    'avgSqrt' : datetime.timedelta(0,avgSqrt),
                    }
        else:
            d = {
                    'avg' : datetime.timedelta(0),
                    'stDev' : datetime.timedelta(0),
                    'zScore' : datetime.timedelta(0),
                    'avgSqrt' : datetime.timedelta(0),
                    }
        return d


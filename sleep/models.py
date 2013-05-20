from django.db import models
from django.contrib.auth.models import User

import datetime
import math

class Sleep(models.Model):
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
            d=sleeper.sleepStats()
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

    def sleepPerDay(self,start=datetime.date.min,end=datetime.date.max):
        sleeps = self.sleep_set.filter(date__gte=start,date__lte=end).values('date','start_time','end_time')
        if sleeps:
            dates=map(lambda x: x['date'], sleeps)
            first = min(dates)
            last = max(dates)
            n = (last-first).days + 1
            dateRange = [first + datetime.timedelta(i) for i in range(0,n)]
            return [sum([(s['end_time']-s['start_time']).total_seconds() for s in filter(lambda x: x['date']==d,sleeps)]) for d in dateRange]
        else:
            return []

    def sleepStats(self,start=datetime.date.min,end=datetime.date.max):
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

    def avgSleep(self,*args,**kwargs):
        return self.sleepStats(*args,**kwargs)['avg']

    def stDevSleep(self,*args,**kwargs):
        return self.sleepStats(*args,**kwargs)['stDev']

    def zScore(self,*args,**kwargs):
        return self.sleepStats(*args,**kwargs)['zScore']

    def avgSqrt(self,*args,**kwargs):
        return self.sleepStats(*args,**kwargs)['avgSqrt']




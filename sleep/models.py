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
        return "%s slept on %s from %s to %s" % (self.user,self.date,self.start_time,self.end_time)


class Sleeper(User):
    class Meta:
        proxy = True

    def timeSlept(self,d):
        sleeps = self.sleep_set.filter(date=d)
        return sum([s.end_time-s.start_time for s in sleeps],datetime.timedelta(0))

    def zScore(self,start=datetime.date.min,end=datetime.date.max):
        sleeps = self.sleep_set.filter(date__gte=start,date__lte=end).values('date','start_time','end_time')
        dates=map(lambda x: x['date'], sleeps)
        first = min(dates)
        last = max(dates)
        n = (last-first).days + 1
        dateRange = [first + datetime.timedelta(i) for i in range(0,n)]
        sleepPerDay = [sum([(s['end_time']-s['start_time']).total_seconds() for s in filter(lambda x: x['date']==d,sleeps)]) for d in dateRange]
        avgSleep = sum(sleepPerDay)/n
        stDevSleep = math.sqrt(sum(map(lambda x: (x-avgSleep)**2, sleepPerDay))/n)
        return datetime.timedelta(0,avgSleep - stDevSleep)




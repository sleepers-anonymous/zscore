from django import template
from django.utils.timezone import localtime
from sleep.models import *
import datetime
register = template.Library()

@register.inclusion_tag('inclusion/graph_per_day.html')
def graphPerDay(user, full=None):
    sleeper = Sleeper.objects.get(pk=user.pk)
    if full == None: s = datetime.date.today() - datetime.timedelta(14)
    elif full == "full": s = datetime.date.min
    return { 'graphData' : sleeper.sleepPerDay(start = s, packDates=True,hours=True) }

@register.inclusion_tag('inclusion/graph_time_of_day_bars.html')
def graphTimeOfDayBars(user):
    sleeper = Sleeper.objects.get(pk=user.pk)
    sleeps = sleeper.sleep_set.all()
    if not sleeps:
        return { 'sleeps' : [] }
    first = min([localtime(s.start_time) for s in sleeps]).date()
    last = max([localtime(s.end_time) for s in sleeps]).date()
    n = (last-first).days + 1
    dateRange = [first + datetime.timedelta(i) for i in range(n)]
    for i in range(n):
        dateRange[i] = (i,dateRange[i])
    times = range(25)
    height = n*15+15
    
    sleepsProcessed = []
    for sleep in sleeps:
        startDate = localtime(sleep.start_time).date()
        endDate = localtime(sleep.end_time).date()
        dr = [startDate + datetime.timedelta(i) for i in range((endDate-startDate).days + 1)]
        for d in dr:
            if d == startDate:
                startTime = localtime(sleep.start_time).time()
            else:
                startTime = datetime.time(0)
            if d == endDate:
                endTime = localtime(sleep.end_time).time()
            else:
                endTime = datetime.time(23,59)
            sleepsProcessed.append((startTime.hour * 15 + startTime.minute / 4., (d-first).days * 15, endTime.hour * 15 + endTime.minute / 4. - startTime.hour * 15 - startTime.minute / 4., 15))

    context = {
            'hassleep': True,
            'sleeps' : sleepsProcessed,
            'dateRange' : dateRange,
            'times' : times,
            'height' : height,
            }
    return context
    
@register.inclusion_tag('inclusion/graph_sleep_times.html')
def graphSleepTimes():
    res = 10
    labels = [""] * (24 * 60 / res)
    for i in range(24):
        labels[i*60/res]=str(i)+":00"
    graphData = Sleep.objects.sleepTimes(res=res)
    return { 'graphData' : graphData, 'labels' : labels }

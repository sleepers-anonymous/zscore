from django import template
from sleep.models import *
import datetime
register = template.Library()

@register.inclusion_tag('inclusion/graph_per_day.html')
def graphPerDay(user, interval=None):
    sleeper = Sleeper.objects.get(pk=user.pk)
    if interval == None: s = datetime.date.min
    else: s = datetime.date.today() - datetime.timedelta(interval)
    graphData = sleeper.sleepPerDay(start = s, packDates=True,hours=True)
    side = min(1000, max(400, len(graphData)//7*200))
    return { 'graphData' : graphData , "side": side}

@register.inclusion_tag('inclusion/graph_time_of_day_bars.html')
def graphTimeOfDayBars(user, interval = None):
    sleeper = Sleeper.objects.get(pk=user.pk)
    sleeps = sleeper.sleep_set.all() if interval == None else sleeper.sleep_set.filter(start_time__gte=(datetime.date.today()-datetime.timedelta(interval)))
    if not sleeps:
        return { 'sleeps' : [] }
    first = min([s.start_time.astimezone(pytz.timezone(s.timezone)) for s in sleeps]).date()
    last = max([s.end_time.astimezone(pytz.timezone(s.timezone)) for s in sleeps]).date()
    n = (last-first).days + 1
    dateRange = [first + datetime.timedelta(i) for i in range(n)]
    for i in range(n):
        dateRange[i] = (i,dateRange[i])
    times = range(25)
    height = n*15+15
    
    sleepsProcessed = []
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
            sleepsProcessed.append((startTime.hour * 15 + startTime.minute / 4., (d-first).days * 15, endTime.hour * 15 + endTime.minute / 4. - startTime.hour * 15 - startTime.minute / 4., 15))

    avgWakeUpTime = sleeper.avgWakeUpTime()
    
    context = {
            'hassleep': True,
            'sleeps' : sleepsProcessed,
            'dateRange' : dateRange,
            'times' : times,
            'height' : height,
            'avgWakeUpTime': avgWakeUpTime,
            }
    return context
    
@register.inclusion_tag('inclusion/graph_sleep_times.html')
def graphSleepTimes(user = None):
    res = 10
    labels = [""] * (24 * 60 / res)
    for i in range(24):
        labels[i*60/res]=str(i)+":00"
    graphData = Sleep.objects.sleepTimes(res=res, user = user) if user != None else Sleep.objects.sleepTimes(res=res)
    return { 'graphData' : graphData, 'labels' : labels }

@register.inclusion_tag('inclusion/graph_sleep_start_end_times.html')
def graphSleepStartEndTimes(user = None):
    res = 60
    labels = [""] * (24 * 60 / res)
    for i in range(24):
        labels[i*60/res]=str(i)+":00"
    start,end = Sleep.objects.sleepStartEndTimes(res=res, user=user) if user != None else Sleep.objects.sleepStartEndTimes(res=res)
    return { 'startData' : start, 'endData' : end, 'labels' : labels }

@register.inclusion_tag('inclusion/graph_sleep_lengths.html')
def graphSleepLengths(user = None):
    res = 60
    hours = 16
    labels = [""] * (hours * 60 / res) + ["16:00+"]
    for i in range(hours):
        labels[i*60/res]=str(i)+":00"
    lengths = Sleep.objects.sleepLengths(res=res, user=user) if user != None else Sleep.objects.sleepLengths(res=res)
    graphData = lengths[:(hours * 60 / res)]
    graphData.append(sum(lengths[(hours*60/res):]))
    return { 'graphData': graphData, 'labels' : labels }

from django import template
from sleep.models import *
import datetime
import pytz
register = template.Library()

# Inclusion tags
@register.inclusion_tag('inclusion/sleep_stats.html',takes_context=True)
def sleepStatsView(context, renderContent='html'):
    user = context['request'].user
    sleeper = Sleeper.objects.get(pk=user.pk)
    timestyle = "%I:%M %p" if sleeper.sleeperprofile.use12HourTime else "%H:%M"
    w =  sleeper.avgWakeUpTime(datetime.date.today()-datetime.timedelta(7), datetime.date.today(), stdev = True)
    if w != None:
        if len(w) == 2: context['wakeup'], context['wakeup_dev'] = w[0].strftime(timestyle), w[1]
        else: context['wakeup'] = w[0].strftime(timestyle)
    sleeptime = sleeper.avgGoToSleepTime(datetime.date.today()-datetime.timedelta(7), datetime.date.today(), stdev = True)
    if sleeptime != None:
        if len(sleeptime) == 2: context["sleeptime"], context["sleeptime_dev"] = sleeptime[0].strftime(timestyle), sleeptime[1]
        else: context["sleeptime"] = sleeptime.strftime(timestyle)
    now = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)
    context['lastDay'] = sleeper.timeSleptByTime(now-datetime.timedelta(1),now)
    context['total'] = sleeper.timeSleptByDate()
    context['renderContent'] = renderContent
    return context

@register.inclusion_tag('inclusion/stats_table.html')
def sleepStatsTable(user):
    context = {}
    sleeper = Sleeper.objects.get(pk=user.pk)
    context['global'] = sleeper.movingStats()
    context['weekly'] = sleeper.movingStats(datetime.date.today()-datetime.timedelta(7),datetime.date.today())
    context['decaying'] = sleeper.decayStats()
    return context

@register.inclusion_tag('inclusion/sleep_list.html', takes_context=True)
def sleepListView(context, renderContent='html'):
    user = context['request'].user
    sleeps = Sleep.objects.filter(user=user).order_by('-start_time', '-end_time')[:20]
    allnighters = Allnighter.objects.filter(user=user).order_by('-date')[:5]
    numdates = Sleep.objects.filter(user=user).values('date').distinct().count()
    numsleeps = Sleep.objects.filter(user=user).count()
    anumdates = Allnighter.objects.filter(user=user).values('date').distinct().count()
    numallnighters = Allnighter.objects.filter(user=user).count()
    return {'sleeps': sleeps,
            'numdates': numdates,
            'numsleeps': numsleeps,
            'allnighters': allnighters,
            'anumdates': anumdates,
            'numallnighters': numallnighters,
            'renderContent': renderContent}

@register.inclusion_tag('inclusion/sleep_entry.html', takes_context=True)
def sleepEntryView(context,renderContent='html'):
    return {'renderContent': renderContent,
            'timezones': [tz[0] for tz in TIMEZONES],
            'mytz': context['request'].user.sleeperprofile.timezone,
            }

@register.inclusion_tag('inclusion/sleep_view_table.html')
def sleepViewTable(request, **kwargs):
    """Prints a tablified list of sleeps: Options: start, end, user, showcomments, showedit, and reverse"""
    settings = {
            "start": datetime.date.min,
            "end": datetime.date.max,
            "user": request.user,
            "showcomments": False,
            "showedit": False,
            "reverse": True,
            "fulldate": False,
            "fullTZ": False,
            "number":None,
            }
    settings.update(kwargs)
    sleepq = settings["user"].sleep_set.filter(start_time__gte=settings["start"], end_time__lte=settings["end"])
    allnighterq = settings["user"].allnighter_set.filter(date__gte=settings["start"], end_time__lte=settings["end"])
    if settings["reverse"]:
        sleepq = sleepq.order_by('-start_time', '-end_time')
        allnighterq = allnighterq.order_by('-start_time', '-end_time')
    else:
        sleepq = sleepq.order_by('start_time', 'end_time')
        allnighterq = allnighterq.order_by('start_time', 'end_time')
    if settings["number"] != None:
        sleepq = sleepq[:settings["number"]]
        allnighter = allnighterq[:settings["number"]]
    prof = request.user.sleeperprofile
    fmt = ("%I:%M %p", "%I:%M %p %x") if prof.use12HourTime else ("%H:%M", "%H:%M %x")
    dfmt = "%A, %B %e, %Y" if settings["fulldate"] else "%D"
    sleeps = []
    for sleep in sleepq:
        if sleep.start_local_time().date() == sleep.end_local_time().date():
            d = {"start_time": sleep.start_local_time().strftime(fmt[0]), "end_time": sleep.end_local_time().strftime(fmt[1]), "date": sleep.date.strftime(dfmt)}
        else:
            d = {"start_time": sleep.start_local_time().strftime(fmt[1]), "end_time": sleep.end_local_time().strftime(fmt[1]), "date": sleep.date.strftime(dfmt)}
        if settings["showcomments"]: d["comments"] = sleep.comments
        sleeps.append(d)
    context = {"sleeps": sleeps}
    return context

@register.simple_tag
def displayUser(username):
    if username != "[redacted]": return '''<a href="/creep/%s/">%s</a>''' % (username , username)
    else: return username

@register.inclusion_tag('inclusion/display_friend.html')
def displayFriend(you,them,requested=False):
    prof = you.sleeperprofile
    friends = (them.pk,) in prof.friends.values_list('pk')
    following = (them.pk,) in prof.follows.values_list('pk')
    context = {
            'you' : you,
            'them' : them,
            'friends' : friends,
            'following' : following,
            'requested' : requested or requested=='True',
            }
    return context

@register.simple_tag
def displayFriendRequests(user):
    fr = FriendRequest.objects.filter(requestee=user,accepted=None)
    if fr: return " <b>(%s)</b>" % fr.count()
    else: return ""

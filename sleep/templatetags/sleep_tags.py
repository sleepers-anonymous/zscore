from django import template
from sleep.models import *
import datetime
import pytz
register = template.Library()

# Inclusion tags
@register.inclusion_tag('inclusion/partial_sleep.html')
def displayPartialButton(user, path = "/", size = 2.25):
    if user.is_authenticated():
        try:
            p = user.partialsleep
            context = {"hasPartial": 1}
        except:
            context = {"hasPartial": 2}
    context["path"] = path
    context["size"] = size
    return context


@register.inclusion_tag('inclusion/sleep_stats.html',takes_context=True)
def sleepStatsView(context, renderContent='html'):
    user = context['request'].user
    sleeper = Sleeper.objects.get(pk=user.pk)
    timestyle = "%I:%M %p" if sleeper.sleeperprofile.use12HourTime else "%H:%M"
    w =  sleeper.avgWakeUpTime(datetime.date.today()-datetime.timedelta(7), datetime.date.today(), stdev = True)
    if w != None:
        if type(w) == tuple: context['wakeup'], context['wakeup_dev'] = w[0].strftime(timestyle), w[1]
        else: context['wakeup'] = w.strftime(timestyle)
    sleeptime = sleeper.avgGoToSleepTime(datetime.date.today()-datetime.timedelta(7), datetime.date.today(), stdev = True)
    if sleeptime != None:
        if type(sleeptime) == tuple: context["sleeptime"], context["sleeptime_dev"] = sleeptime[0].strftime(timestyle), sleeptime[1]
        else: context["sleeptime"] = sleeptime.strftime(timestyle)
    now = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)
    context['lastDay'] = sleeper.timeSleptByTime(now-datetime.timedelta(1),now)
    context['total'] = sleeper.timeSleptByDate()
    context['renderContent'] = renderContent
    return context

@register.inclusion_tag('inclusion/stats_table.html')
def sleepStatsTable(user):
    sleeper = Sleeper.objects.get(pk=user.pk)
    context = {'global': sleeper.movingStats(),
            'weekly': sleeper.movingStats(datetime.date.today()-datetime.timedelta(7),datetime.date.today()),
            'decaying': sleeper.decayStats(),
    }
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
            'renderContent': renderContent,
            'use12HourTime': user.sleeperprofile.use12HourTime,
            }

@register.inclusion_tag('inclusion/sleep_entry.html', takes_context=True)
def sleepEntryView(context,renderContent='html'):
    return {'renderContent': renderContent,
            'timezones': [tz[0] for tz in TIMEZONES],
            'mytz': context['request'].user.sleeperprofile.timezone,
            }

@register.inclusion_tag('inclusion/display_sleep.html')
def displaySleep(sleep, **kwargs):
    """Prints a tablified sleep. Options: showcomments, showedit, fulldate, showTZ, use12HourTime"""
    settings = {
            "showcomments": False,
            "showedit": False,
            "fulldate": False,
            "showTZ": 0, #0 for no TZ, 1 for short TZ, 2 for full TZ
            "use12HourTime": False,
            }
    settings.update(kwargs)
    fmt = ("%I:%M %p", "%I:%M %p %x") if settings["use12HourTime"] else ("%H:%M", "%H:%M %x")
    dfmt = "%A, %B %e, %Y" if settings["fulldate"] else "%B %e"
    if sleep.start_local_time().date() == sleep.end_local_time().date() or sleep.start_local_time().date() == sleep.date: d = {"start_time": sleep.start_local_time().strftime(fmt[0])}
    else: d = {"start_time": sleep.start_local_time().strftime(fmt[1])}
    if sleep.end_local_time().date() == sleep.date: d["end_time"] = sleep.end_local_time().strftime(fmt[0])
    else: d["end_time"] = sleep.end_local_time().strftime(fmt[1])
    d["date"] = sleep.date.strftime(dfmt)
    if settings["showcomments"]:
        if sleep.comments != "": d["comments"] = sleep.comments
    if settings["showTZ"] == 1: d["TZ"] = sleep.getTZShortName()
    elif settings["showTZ"] == 2: d["TZ"] = sleep.timezone
    d["length"] = sleep.length()
    d["showedit"] = settings["showedit"]
    d["pk"] = sleep.pk
    return d

@register.inclusion_tag('inclusion/display_allnighter.html')
def displayAllNighter(allnighter, **kwargs):
    """Prints a tablified allnighter. Options: showcomments, showedit, fulldate"""
    settings = {
            "showcomments": False,
            "showedit": False,
            "fulldate": False,
            }
    settings.update(kwargs)
    dfmt = "%A, %B %e, %Y" if settings["fulldate"] else "%B %e"
    d = {"date": allnighter.date.strftime(dfmt),
        "pk": allnighter.pk,
        "showedit":settings["showedit"]}
    if settings["showcomments"]:
        if allnighter.comments != "": d["comments"] = allnighter.comments
    return d

@register.inclusion_tag('inclusion/sleep_view_table.html')
def sleepViewTable(request, **kwargs):
    """Prints a tablified list of sleeps: Options: start, end, user, showcomments, showedit, reverse, fulldate, and showTZ"""
    settings = {
            "start": datetime.date.min,
            "end": datetime.date.max,
            "user": request.user,
            "showcomments": False,
            "showedit": False,
            "reverse": True,
            "fulldate": False,
            "showTZ": 0, #0 for no TZ, 1 for short TZ, 2 for full TZ
            "number":None,
            "showallnighters": True
            }
    settings.update(kwargs)
    sleepq = settings["user"].sleep_set.filter(start_time__gte=settings["start"], end_time__lte=settings["end"])
    if settings["showallnighters"]: allnighterq = settings["user"].allnighter_set.filter(date__gte=settings["start"], end_time__lte=settings["end"])
    if settings["reverse"]:
        sleepq = sleepq.order_by('-start_time', '-end_time')
        if settings["showallnighters"]: allnighterq = allnighterq.order_by('-start_time', '-end_time')
    else:
        sleepq = sleepq.order_by('start_time', 'end_time')
        if settings["showallnighters"]: allnighterq = allnighterq.order_by('start_time', 'end_time')
    if settings["number"] != None:
        sleepq = sleepq[:settings["number"]]
        if settings["showallnighters"]: allnighterq = allnighterq[:settings["number"]]
    context = {"use12HourTime":request.user.sleeperprofile.use12HourTime, "showcomments": settings["showcomments"], "showedit":settings["showedit"], "fulldate": settings["fulldate"], "showTZ": settings["showTZ"]}
    if settings["showallnighters"]:
        pass

@register.simple_tag
def displayUser(username):
    if username != "[redacted]": return '''<a href="/creep/%s/">%s</a>''' % (username , username)
    else: return username

@register.inclusion_tag('inclusion/display_my_group.html')
def displayMyGroup(group):
    return {'group' : group}

@register.inclusion_tag('inclusion/display_group_member.html',takes_context=True)
def displayGroupMember(context,group,user):
    context.update({
            'group' : group,
            'user' : user,
            'member' : user in group.members.all(),
            })
    return context

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

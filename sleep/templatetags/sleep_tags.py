from django import template
from sleep.models import *
from django.utils.timezone import now
from django.utils.html import format_html
import datetime
import datetime_utils
import pytz
import numpy
import cmath
register = template.Library()

# Inclusion tags
@register.inclusion_tag('inclusion/announcement.html')
def displayAnnouncements():
    return {'announcements': Announcement.objects.filter(active=True)}

@register.inclusion_tag('inclusion/partial_sleep.html', takes_context=True)
def displayPartialButton(context, user):
    try:
        p = user.partialsleep
        context['has_partial'] = True
    except PartialSleep.DoesNotExist:
        context['has_partial'] = False
    return context


@register.inclusion_tag('inclusion/is_asleep.html', takes_context=True)
def isAsleep(context, you, them):
    p = them.sleeperprofile
    if you.is_authenticated() and them.is_authenticated() and you.pk == them.pk and "as" in context["request"].GET:
        priv = p.checkPermissions(context["request"].GET["as"])
    else:
        priv = p.getPermissions(you)
    if priv >= p.PRIVACY_MAX: #In case, for some goddamn reason, someone defines a privacy setting higher than PRIVACY_MAX
        try:
            partial = them.partialsleep
            newcontext =  {"asleep": "probably asleep"}
        except PartialSleep.DoesNotExist:
            if p.isLikelyAsleep(): newcontext = {"asleep": "likely asleep"}
            else: newcontext =  {"asleep": "probably awake"}
        newcontext["user"] = them
        return newcontext
    else:
        return {}

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
    n = now()
    context['lastDay'] = sleeper.timeSleptByTime(n-datetime.timedelta(1),n)
    context['total'] = sleeper.timeSleptByDate()
    context['renderContent'] = renderContent
    return context

@register.inclusion_tag('inclusion/stats_table.html')
def sleepStatsTable(user):
    sleeper = Sleeper.objects.get(pk=user.pk)
    userMetrics = user.sleeperprofile.metrics.all()
    context = {'global': sleeper.movingStats(),
            'weekly': sleeper.movingStats(datetime.date.today()-datetime.timedelta(7),datetime.date.today()),
            'decaying': sleeper.decayStats(),
            'userMetrics': userMetrics
    }
    return context

@register.inclusion_tag('inclusion/sleep_list.html', takes_context=True)
def sleepListView(context, renderContent='html'):
    user = context['request'].user
    sleeps = Sleep.objects.filter(user=user).order_by('-start_time', '-end_time')
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

@register.inclusion_tag('inclusion/display_request.html')
def displayRequest(r):
    return {"user": r.user, "r": r}

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
    if username != "[redacted]":
        return format_html('<a href="/creep/{}/">{}</a>', username, username)
    else:
        return username

@register.inclusion_tag('inclusion/display_my_group.html')
def displayMyGroup(group, amMember = 0):
    return {'group' : group, 'amMember' : amMember, 'isPublic': group.privacy >= group.PUBLIC}

@register.inclusion_tag('inclusion/display_group_member.html', takes_context= True)
def displayGroupMember(context, group, user):
    ms = Membership.objects.filter(user = user, group = group)
    newcontext = {}
    if ms.count() >= 1:
        m = ms[0]
        newcontext["isMember"] = True
        newcontext["admin"] = (m.role >= m.ADMIN)
        newcontext["isAdmin"] = context["isAdmin"]
    newcontext.update({
            'group' : group,
            'user' : user,
            'canremove': context['isAdmin'] or context["request"].user == user,
            'you': context["request"].user,
            })
    return newcontext

@register.inclusion_tag('inclusion/display_invite.html')
def displayInvite(invite):
    return {'invite' : invite}

@register.simple_tag
def displayInvites(user):
    num_invites = user.groupinvite_set.filter(accepted=None).count()
    if num_invites:
        return format_html(" <b>({})</b>", num_invites)
    else:
        return ""

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
    num_requests = user.friendrequest_set.filter(accepted=None).count()
    if num_requests:
        return format_html(" <b>({})</b>", num_requests)
    else:
        return ""

@register.filter
def getScore(statdict, metric):
    try:
        v = statdict[metric.name]
        if metric.display_style == 'asHHMM':
            return datetime_utils.printHHMM(v)
        elif metric.display_style == 'asInt':
            return v
        else:
            return ''
    except:
        return ''

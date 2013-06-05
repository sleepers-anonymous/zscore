from django import template
from sleep.models import Sleeper, Sleep
import datetime
register = template.Library()

# Inclusion tags
@register.inclusion_tag('inclusion/sleep_stats.html',takes_context=True)
def sleepStatsView(context, renderContent='html'):
    user = context['request'].user
    sleeper = Sleeper.objects.get(pk=user.pk)
    timestyle = "%I:%M %p" if sleeper.getOrCreateProfile().use12HourTime else "%H:%M"
    w =  sleeper.avgWakeUpTime(datetime.date.today()-datetime.timedelta(7), datetime.date.today())
    if w != None: context['wakeup'] = w.strftime(timestyle)
    context['total'] = sleeper.timeSlept()
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
    numdates = Sleep.objects.filter(user=user).values('date').distinct().count()
    numsleeps = Sleep.objects.filter(user=user).count()
    return {'sleeps': sleeps,
            'numdates': numdates,
            'numsleeps': numsleeps,
            'renderContent': renderContent}
@register.inclusion_tag('inclusion/sleep_entry.html')
def sleepEntryView(renderContent='html'):
    return {'renderContent': renderContent}

@register.simple_tag
def displayUser(username):
    if username != "[redacted]":
        return '''<a href="/creep/%s/">%s</a>''' % (username , username)
    else:
        return username

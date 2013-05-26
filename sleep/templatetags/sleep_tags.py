from django import template
from sleep.models import Sleeper, Sleep
import datetime
register = template.Library()

# Inclusion tags
@register.inclusion_tag('inclusion/sleep_stats.html',takes_context=True)
def sleepStatsView(context):
    user = context['request'].user
    sleeper = Sleeper.objects.get(pk=user.pk)
    context['global']=sleeper.movingStats()
    context['weekly']=sleeper.movingStats(datetime.date.today()-datetime.timedelta(7),datetime.date.today())
    context['decaying']=sleeper.decayStats()
    context['total']=sleeper.timeSlept()
    return context
@register.inclusion_tag('inclusion/sleep_list.html', takes_context=True)
def sleepListView(context):
    user = context['request'].user
    sleeps = Sleep.objects.filter(user=user).order_by('-start_time', '-end_time')[:20]
    numdates = Sleep.objects.filter(user=user).values('date').distinct().count()
    numsleeps = Sleep.objects.filter(user=user).count()
    return {'sleeps': sleeps, 'numdates': numdates, 'numsleeps': numsleeps}
@register.inclusion_tag('inclusion/sleep_entry.html')
def sleepEntryView():
    # No context needed
    return {}

@register.simple_tag
def displayUser(username):
    if username != "[redacted]":
        return '''<a href="/creep/%s/">%s</a>''' % (username , username)
    else:
        return username

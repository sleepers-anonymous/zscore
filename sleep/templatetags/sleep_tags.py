from django import template
from sleep.models import Sleeper
import datetime
register = template.Library()

# Inclusion tags
@register.inclusion_tag('inclusion/stats.html',takes_context=True)
def statsView(context):
    user = context['request'].user
    sleeper = Sleeper.objects.get(pk=user.pk)
    context['global']=sleeper.sleepStats()
    context['weekly']=sleeper.sleepStats(datetime.date.today()-datetime.timedelta(7),datetime.date.today())
    return context
@register.inclusion_tag('inclusion/sleep_list.html')
def sleepListView():
    # Return an empty context for now
    return {}
@register.inclusion_tag('inclusion/sleep_entry.html')
def sleepEntryView():
    # No context needed
    return {}

from django import template
from sleep.models import *
import datetime
register = template.Library()

@register.inclusion_tag('inclusion/graph_per_day.html')
def graphPerDay(user):
    sleeper = Sleeper.objects.get(pk=user.pk)
    return { 'graphData' : sleeper.sleepPerDay(packDates=True,hours=True) }

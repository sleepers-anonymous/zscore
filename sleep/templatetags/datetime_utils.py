from django import template
import datetime
register = template.Library()

@register.filter(name='printHHMM')
def printHHMM(value):
    '''takes a datetime and prints it as HH:MM'''
    return ':'.join(str(value).split(':')[:2])


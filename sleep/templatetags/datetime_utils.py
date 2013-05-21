from django import template
import datetime
register = template.Library()

@register.filter(name='printHHMM')
def printHHMM(value):
    '''takes a datetime and prints it as HH:MM'''
    return ':'.join(str(value).split(':')[:2])

@register.filter(name='printDHM')
def printDHM(value):
    '''takes a datetime and prints it as HH:MM'''
    parts=[]
    if ',' in str(value):
        d,t=str(value).split(',')
        parts.append(d)
    else:
        t=str(value)
    h,m,s=t.split(':')
    if int(h)==1:
        parts.append("1 hour")
    elif int(h)>1:
        parts.append(h.strip()+" hours")
    if int(m)==1:
        parts.append("1 minute")
    elif int(m)>1:
        parts.append(m.strip()+" minutes")
    if len(parts)==0:
        return "none"
    elif len(parts)==1:
        return parts[0]
    elif len(parts)==2:
        return parts[0]+" and "+parts[1]
    elif len(parts)==3:
        return parts[0]+", "+parts[1]+", and "+parts[2]


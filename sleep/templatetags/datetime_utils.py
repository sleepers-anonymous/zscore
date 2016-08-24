from django import template
import datetime
register = template.Library()

@register.filter(name='printHHMM')
def printHHMM(value):
    '''takes a datetime.timedelta and prints it as HH:MM'''
    s=int(value.total_seconds())
    if s<0: #so we round towards zero rather than towards -Infinity
        sign="-"
        s=-s
    else:
        sign=""
    h,s=divmod(s,3600)
    m,s=divmod(s,60)
    return "%s%d:%02d" % (sign,h,m)

@register.filter(name='printDHHMM')
def printDHHMM(value):
    '''takes a datetime.timedelta and prints it as D days, HH:MM'''
    s=int(value.total_seconds())
    if s<0: #so we round towards zero rather than towards -Infinity
        sign="-"
        s=-s
    else:
        sign=""
    d,s=divmod(s,86400)
    h,s=divmod(s,3600)
    m,s=divmod(s,60)
    if d==1:
        return "%s%d day, %d:%02d" % (sign,d,h,m)
    elif d>1:
        return "%s%d days, %d:%02d" % (sign,d,h,m)
    return "%s%d:%02d" % (sign,h,m)

@register.filter(name='printYDHM')
def printYDHM(value,useYear=True):
    '''takes a datetime.timedelta and prints it as Y year(s), D day(s), H hour(s), and M minute(s)'''
    s=int(value.total_seconds())
    if s<0: #so we round towards zero rather than towards -Infinity
        sign="negative "
        s=-s
    else:
        sign=""
    if useYear:
        y,s=divmod(s,31566240)
    d,s=divmod(s,86400)
    h,s=divmod(s,3600)
    m,s=divmod(s,60)
    parts=[]
    if useYear:
        if y==1:
            parts.append("1 year")
        elif y>1:
            parts.append(str(y)+" years")
    if d==1:
        parts.append("1 day")
    elif d>1:
        parts.append(str(d)+" days")
    if h==1:
        parts.append("1 hour")
    elif h>1:
        parts.append(str(h)+" hours")
    if m==1:
        parts.append("1 minute")
    elif m>1:
        parts.append(str(m)+" minutes")
    if len(parts)==0:
        return "none"
    elif len(parts)==1:
        return sign+parts[0]
    else:
        return sign+", ".join(parts[:-1])+" and "+parts[-1]


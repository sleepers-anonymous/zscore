from django import template
from sleep.models import *
register = template.Library()

@register.inclusion_tag('inclusion/gravatar.html')
def gravatar(you, them, size = 60):
    d = "mm" #default is mysteryman
    size = str(size)
    try:
        p = SleeperProfile.objects.get(user=them)
        priv = p.getPermissions(you)
        if priv <= p.PRIVACY_REDACTED: return {"url": "https://secure.gravatar.com/avatar/205e460b479e2e5b48aec07710c08d50?f=y&d=" + d + "&s=" + size}
        email = p.getEmailHash()
        if email == None: return {"url": "https://secure.gravatar.com/avatar/205e460b479e2e5b48aec07710c08d50?f=y&d=" + d + "&s=" + size}
        else: return {"url": "https://secure.gravatar.com/avatar/" + email + "?d="+d + "&s=" + size}
    except:
        return {"url": "https://secure.gravatar.com/avatar/205e460b479e2e5b48aec07710c08d50?f=y&d=" + d + "&s=" + size}

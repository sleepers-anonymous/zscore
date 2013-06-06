from django.utils import timezone
from models import SleeperProfile, Sleeper

import pytz

class TimezoneMiddleware(object):
    def process_request(self,request):
        if request.user.is_authenticated():
            sleeper = Sleeper.objects.get(pk=request.user.pk)
            prof = sleeper.getOrCreateProfile()
            tz = pytz.timezone(prof.timezone)
            timezone.activate(tz)

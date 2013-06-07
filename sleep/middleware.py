from django.utils import timezone
from models import SleeperProfile, Sleeper

import pytz

class TimezoneMiddleware(object):
    def process_request(self,request):
        if request.user.is_authenticated():
            tz = pytz.timezone(request.user.sleeperprofile.timezone)
            timezone.activate(tz)

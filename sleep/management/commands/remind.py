from django.core.management.base import BaseCommand, CommandError
from django.utils.timezone import now
from django.core.mail import EmailMultiAlternatives

from sleep.models import SleeperProfile

import datetime, pytz

class Command(BaseCommand):
    help = "Reminds all users who have a reminder set for the next hour"

    def handle(self, *args, **options):
        profs = SleeperProfile.objects.filter(emailreminders = True)
        n = now()
        for p in profs:
            raise NotImplemented
            

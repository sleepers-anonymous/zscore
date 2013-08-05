from django.core.management.base import BaseCommand, CommandError
from sleep.models import SleeperGroup

class Command(BaseCommand):
    help = "Removes all empty groups"

    def handle(self, *args, **options):
        groups = SleeperGroup.objects.all()
        for g in groups:
            if g.membership_set.all().count() == 0:
                self.stdout.write('Removing group %s' % g)
                g.delete()

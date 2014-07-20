#For things that don't fit in anywhere else

from django.db import models
from django.core.cache import cache
from django.core.cache.utils import make_template_fragment_key

class Announcement(models.Model):
    name = models.CharField(max_length=40)
    description = models.TextField(blank=True)
    active = models.BooleanField(default=True)

    def __unicode__(self):
        isActive = ' (Active)' if self.active else ''
        return self.name + ': ' + self.description + isActive

    def save(self, *args, **kwargs):
        cache.delete_many([make_template_fragment_key('header', (user.username,)) for user in Sleeper.objects.all()])
        super(Announcement, self).save(*args, **kwargs)

    class Meta:
        app_label = 'sleep'
        db_table = 'sleep_announcement'

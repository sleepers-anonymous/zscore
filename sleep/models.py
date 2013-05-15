from django.db import models
from django.contrib.auth.models import User

class Sleep(models.Model):
    user = models.ForeignKey(User)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    comments = models.TextField()
    date = models.DateField()

    def __unicode__(self):
        return "%s slept from %s to %s" % (self.user,self.start_time,self.end_time)

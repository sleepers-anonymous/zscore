from django.http import HttpResponseRedirect
from django.shortcuts import render
from users.forms import UserEmailCreationForm
from sleep.models import SleeperProfile
from sleep.models import Metric

def create(request):
    if request.method == 'POST':
        form = UserEmailCreationForm(request.POST)
        if form.is_valid():
            new_user = form.save()
            s = SleeperProfile.objects.get_or_create(user=new_user)[0]
            for m in Metric.objects.filter(show_by_default=True):
                s.metrics.add(m)
            s.save()
            return HttpResponseRedirect("/")
    else:
        form = UserEmailCreationForm()
    return render(request, "users/create.html", {'form': form})

def profile(request):
    return HttpResponseRedirect("/mysleep")

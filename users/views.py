from django.http import HttpResponseRedirect
from django.shortcuts import render
from users.forms import UserEmailCreationForm
from sleep.models import SleeperProfile

def create(request):
    if request.method == 'POST':
        form = UserEmailCreationForm(request.POST)
        if form.is_valid():
            new_user = form.save()
            SleeperProfile.objects.get_or_create(user=new_user)
            return HttpResponseRedirect("/")
    else:
        form = UserEmailCreationForm()
    return render(request, "users/create.html", {'form': form})

def profile(request):
    return HttpResponseRedirect("/mysleep")

from django.http import HttpResponseRedirect
from django.shortcuts import render
from users.forms import UserEmailCreationForm

def create(request):
    if request.method == 'POST':
        form = UserEmailCreationForm(request.POST)
        if form.is_valid():
            new_user = form.save()
            return HttpResponseRedirect("/")
    else:
        form = UserEmailCreationForm()
    return render(request, "users/create.html", {'form': form})

def profile(request):
    return HttpResponseRedirect("/mysleep")

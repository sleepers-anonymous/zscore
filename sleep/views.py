from django.template import RequestContext
from django.template.loader import render_to_string
from django.http import *
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.core import serializers
from django.db.models import Q
from django.core.exceptions import ValidationError

from sleep.models import *
from sleep.forms import *

import datetime
import pytz

def home(request):
    return render(request, 'index.html')

def faq(request):
    return render(request, 'faq.html')

@login_required
def mysleep(request):
    return HttpResponse(render_to_string('sleep/mysleep.html',{},context_instance=RequestContext(request)))

@login_required
def editOrCreateSleep(request,sleep = None):
    context = {}
    create = False
    if sleep:
        sleep = Sleep.objects.filter(pk=sleep)
        if sleep.count() != 1:  return render(request, "editsleepfailed.html")
    else: create = True
    user = Sleeper.objects.get(pk=request.user.pk)
    tformat = "%I:%M %p %x" if user.getOrCreateProfile().use12HourTime else "%H:%M %x" 
    if not(create) and sleep[0].user.pk != user.pk: return render(request, "editsleepfailed.html")
    if request.method == 'POST':
        if create: form = UpdateSleepForm(request.POST)
        else: form = UpdateSleepForm(request.POST, instance=sleep[0])
        try:
            if create:
                newsleep = form.save(commit=False)
                newsleep.user_id= user.id
                newsleep.full_clean()
                newsleep.save()
                form = UpdateSleepForm(instance=newsleep)
            else:
                try:
                    form.is_valid()
                except AttributeError:
                    raise ValidationError("Overlapping Sleep Detected!")
                form.save()
                context["sleep"] = sleep[0]
            context["successfulSave"] = True
            context["form"] = form
            if create: return HttpResponse(render_to_string('simplecreation.html', context, context_instance=RequestContext(request)))
            context.update({ "start": sleep[0].start_time.strftime(tformat), "end": sleep[0].end_time.strftime(tformat)})
            return HttpResponse(render_to_string('editsleep.html',context,context_instance=RequestContext(request)))
        except ValidationError, e:
            print e
            if "forceOverlap" in request.POST and request.POST['forceOverlap'] == 'on':
                if create:
                    newsleep = form.save(commit=False)
                    newsleep.user_id = user.id
                    newsleep.save()
                    form = UpdateSleepForm(instance=newsleep)
                else:
                    form.save()
                    context["sleep"] = sleep[0]
                context["successfulSave"] = True
            else:
                if hasattr(e, "message_dict"): context["saveError"] = "; ".join(e.message_dict["__all__"]).encode("ascii", "ignore")
                if hasattr(e, "messages"): context["saveError"]= "; ".join(e.messages).encode("ascii", "ignore")
                context["successfulSave"] = False
            context["form"] = form
            if create: return HttpResponse(render_to_string('simplecreation.html', context, context_instance=RequestContext(request)))
            context.update({ "start": sleep[0].start_time.strftime(tformat), "end": sleep[0].end_time.strftime(tformat)})
            return HttpResponse(render_to_string('editsleep.html', context, context_instance=RequestContext(request)))
    else:
        if create:
            today = datetime.date.today().strftime("%m/%d/%Y")
            initial = {"start_time": today + " 00:00",
                        "end_time": today + " 00:00",
                        "date": today,
                        "timezone":user.getOrCreateProfile().timezone,
                        }
            form = UpdateSleepForm(initial = initial)
            context.update({"form":form})
            return HttpResponse(render_to_string('simplecreation.html', context, context_instance=RequestContext(request)))
        else: form = UpdateSleepForm(instance = sleep[0])
        context.update({"form":form, "sleep": sleep[0], "start": sleep[0].start_time.strftime(tformat), "end": sleep[0].end_time.strftime(tformat)})
        return HttpResponse(render_to_string('editsleep.html', context, context_instance=RequestContext(request)))

def leaderboard(request,sortBy='zScore'):
    if sortBy not in ['zScore','avg','avgSqrt','avgLog','avgRecip','stDev']:
        sortBy='zScore'
    ss = Sleeper.objects.sorted_sleepers(sortBy,request.user)
    top = [ s for s in ss if s['rank']<=10 or request.user.is_authenticated() and s['user'].pk==request.user.pk ]
    now = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)
    lastDayWinner = Sleeper.objects.bestByTime(now-datetime.timedelta(1),now,request.user)[0]
    context = {
            'top' : top,
            'lastDayWinner' : lastDayWinner,
            'total' : Sleep.objects.totalSleep(),
            'number' : Sleep.objects.all().values_list('user').distinct().count(),
            }
    return HttpResponse(render_to_string('leaderboard.html',context,context_instance=RequestContext(request)))

def creep(request,username=None, asOther=None):
    if not username:
        if request.user.is_anonymous():
            creepable=Sleeper.objects.filter(sleeperprofile__privacy__gte=SleeperProfile.PRIVACY_STATS)
            followed = []
        else:
            creepable=Sleeper.objects.filter(
                    Q(sleeperprofile__privacyLoggedIn__gte=SleeperProfile.PRIVACY_STATS) | 
                    (
                        Q(sleeperprofile__privacyFriends__gte=SleeperProfile.PRIVACY_STATS) &
                        Q(sleeperprofile__friends=request.user)
                    )
                )
            sleeper = Sleeper.objects.get(pk=request.user.pk)
            prof = sleeper.getOrCreateProfile()
            followed = prof.follows.order_by('username')
        total=creepable.distinct().count()
        if request.method == 'POST':
            form=CreepSearchForm(request.POST)
            if form.is_valid():
                users = creepable.filter(username__icontains=form.cleaned_data['username']).distinct()
                count = users.count()
                if count==1:
                    return HttpResponseRedirect('/creep/%s/' % users[0].username)
                else: 
                    context = {
                            'results' : users,
                            'count' : count,
                            'form' : form,
                            'new' : False,
                            'total' : total,
                            'followed' : followed,
                            }
                    return HttpResponse(render_to_string('creepsearch.html',context,context_instance=RequestContext(request)))
        else:
            form = CreepSearchForm()
        context = {
                'form' : form,
                'new' : True,
                'total' : total,
                'followed' : followed,
                }
        return HttpResponse(render_to_string('creepsearch.html',context,context_instance=RequestContext(request)))
    else:
        context = {}
        try:
            user=Sleeper.objects.get(username=username)
            p = user.getOrCreateProfile()
            if user.is_anonymous():
                priv = p.privacy
            elif request.user.pk == user.pk:
                priv = p.PRIVACY_PUBLIC
                context["isself"] =True
            elif request.user in p.friends.all():
                priv = p.privacyFriends
            else:
                priv = p.privacyLoggedIn
            if asOther:
                otherD = {"friends":p.privacyFriends, "user": p.privacyLoggedIn,"anon": p.privacy}
                if asOther in otherD: priv = min(priv, otherD[asOther])
            if priv<=p.PRIVACY_NORMAL:
                return HttpResponse(render_to_string('creepfailed.html',{},context_instance=RequestContext(request)))
        except:
            return HttpResponse(render_to_string('creepfailed.html',{},context_instance=RequestContext(request)))
        context.update({'user' : user,'global' : user.decayStats()})
        if priv>=p.PRIVACY_PUBLIC:
            context['sleeps']=user.sleep_set.all().order_by('-end_time')
        return HttpResponse(render_to_string('creep.html',context,context_instance=RequestContext(request)))

@login_required
def editProfile(request):
    sleeper = Sleeper.objects.get(pk=request.user.pk)
    p = sleeper.getOrCreateProfile()
    if request.method == 'POST':
        form = SleeperProfileForm(request.POST, instance=p)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect('/editprofile/')
    else:
        form = SleeperProfileForm(instance=p)

    return HttpResponse(render_to_string('editprofile.html', {'form': form},context_instance=RequestContext(request)))

@login_required
def friends(request):
    sleeper = Sleeper.objects.get(pk=request.user.pk)
    prof = sleeper.getOrCreateProfile()
    friendfollow = (prof.friends.all() | prof.follows.all()).distinct().order_by('username')
    requests = sleeper.requests.filter(friendrequest__accepted=None).order_by('user__username')
    if request.method == 'POST':
        form=FriendSearchForm(request.POST)
        if form.is_valid():
            users = User.objects.filter(username__icontains=form.cleaned_data['username']).exclude(pk=request.user.pk).distinct()
            count = users.count()
            context = {
                    'results' : users,
                    'count' : count,
                    'form' : form,
                    'new' : False,
                    'friendfollow' : friendfollow,
                    'requests' : requests,
                    }
            return HttpResponse(render_to_string('friends.html',context,context_instance=RequestContext(request)))
    else:
        form = FriendSearchForm()
    context = {
            'form' : form,
            'new' : True,
            'friendfollow' : friendfollow,
            'requests' : requests,
            }
    return HttpResponse(render_to_string('friends.html',context,context_instance=RequestContext(request)))
            
@login_required
def requestFriend(request):
    if 'id' in request.POST:
        i = request.POST['id']
        if i==request.user.pk or len(User.objects.filter(pk=i))!=1:
            return HttpResponseNotFound('')
        sleeper = Sleeper.objects.get(pk=request.user.pk)
        prof = sleeper.getOrCreateProfile()
        them = Sleeper.objects.get(pk=i)
        if not FriendRequest.objects.filter(requestor=prof,requestee=them):
            themProf = them.getOrCreateProfile()
            if request.user in themProf.friends.all():
                accept = True
            else:
                accept = None
            FriendRequest.objects.create(requestor=prof,requestee=them,accepted=accept)
        return HttpResponse('')
    else:
        return HttpResponseBadRequest('')

@login_required
def hideRequest(request):
    if 'id' in request.POST:
        i = request.POST['id']
        if i==request.user.pk or len(User.objects.filter(pk=i))!=1:
            return HttpResponseNotFound('')
        frs = FriendRequest.objects.filter(requestor__user__pk=i,requestee=request.user)
        for fr in frs:
            fr.accepted=False
            fr.save()
        return HttpResponse('')
    else:
        return HttpResponseBadRequest('')

@login_required
def addFriend(request):
    if 'id' in request.POST:
        i = request.POST['id']
        if i==request.user.pk or len(User.objects.filter(pk=i))!=1:
            return HttpResponseNotFound('')
        sleeper = Sleeper.objects.get(pk=request.user.pk)
        prof = sleeper.getOrCreateProfile()
        prof.friends.add(i)
        prof.save()
        frs = FriendRequest.objects.filter(requestor__user__pk=i,requestee=request.user)
        for fr in frs:
            fr.accepted=True
            fr.save()
        return HttpResponse('')
    else:
        return HttpResponseBadRequest('')

@login_required
def removeFriend(request):
    if 'id' in request.POST:
        i = request.POST['id']
        if i==request.user.pk or len(User.objects.filter(pk=i))!=1:
            return HttpResponseNotFound('')
        sleeper = Sleeper.objects.get(pk=request.user.pk)
        prof = sleeper.getOrCreateProfile()
        prof.friends.remove(i)
        return HttpResponse('')
    else:
        return HttpResponseBadRequest('')

@login_required
def follow(request):
    if 'id' in request.POST:
        i = request.POST['id']
        if i==request.user.pk or len(User.objects.filter(pk=i))!=1:
            return HttpResponseNotFound('')
        sleeper = Sleeper.objects.get(pk=request.user.pk)
        prof = sleeper.getOrCreateProfile()
        prof.follows.add(i)
        prof.save()
        return HttpResponse('')
    else:
        return HttpResponseBadRequest('')

@login_required
def unfollow(request):
    if 'id' in request.POST:
        i = request.POST['id']
        if i==request.user.pk or len(User.objects.filter(pk=i))!=1:
            return HttpResponseNotFound('')
        sleeper = Sleeper.objects.get(pk=request.user.pk)
        prof = sleeper.getOrCreateProfile()
        prof.follows.remove(i)
        return HttpResponse('')
    else:
        return HttpResponseBadRequest('')

@login_required
def createSleep(request):
    # Date-ify start, end, and center
    timezone = pytz.timezone(request.POST['timezone'])
    start = datetime.datetime(*(map(int, request.POST.getlist("start[]"))))
    start=timezone.localize(start)
    end = datetime.datetime(*(map(int, request.POST.getlist("end[]"))))
    end=timezone.localize(end)
    date = datetime.date(*(map(int, request.POST.getlist("date[]"))[:3]))
    # Pull out comments
    if "comments" in request.POST:
        comments = request.POST["comments"]
    else:
        comments = ""
    # Create the Sleep instance
    Sleep.objects.create(user=request.user, start_time=start, end_time=end, comments=comments, date=date,timezone=timezone)
    return HttpResponse('')

@login_required
def deleteSleep(request):
    if 'id' in request.POST:
        i = request.POST['id']
        s = Sleep.objects.filter(pk=i)
        if len(s) == 0:
            return HttpResponseNotFound('')
        s = s[0]
        if s.user != request.user:
            return HttpResponseForbidden('')
        s.delete()
        return HttpResponse('')
    return HttpResponseBadRequest('')

@login_required
def getSleepsJSON(request):
    u = request.user
    sleeps = list(Sleep.objects.filter(user=u))
    for sleep in sleeps:
        tz = pytz.timezone(sleep.timezone)
        #warning: the following is kind of hacky but it's better than dealing with the timezones in JS.  JS doesn't understand timezones, so we convert the timezone server-side, then pass it through to JS without telling the JS what timezone it's in.  JS interprets it as local time, which is slightly incorrect but works since all we want to do is get the hours/minutes/seconds back out as local time.
        sleep.start_time=sleep.start_time.astimezone(tz).replace(tzinfo=None)
        sleep.end_time=sleep.end_time.astimezone(tz).replace(tzinfo=None)
    data = serializers.serialize('json', sleeps)
    return HttpResponse(data, mimetype='application/json')

from django.template import RequestContext
from django.template.loader import render_to_string
from django.http import *
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, render_to_response
from django.core import serializers
from django.db.models import Q
from django.db import IntegrityError
from django.core.exceptions import *
from django.utils.timezone import now
from django.core.cache import cache

from sleep.models import *
from sleep.forms import *

import datetime
import pytz
import csv

def home(request):
    return render(request, 'index.html')

def faq(request):
    return render(request, 'faq.html')

def privacy(request):
    return render(request, 'privacy.html')

@login_required
def mysleep(request):
    return render_to_response('sleep/mysleep.html',{},context_instance=RequestContext(request))

@login_required
def editOrCreateAllnighter(request, allNighter = None, success=False):
    context = {'success': success}
    prof = request.user.sleeperprofile
    defaulttz = prof.timezone
    if allNighter: #We're editing an allnighter
        context = {"editing": True}
        try:
            a = Allnighter.objects.get(pk=allNighter)
            if a.user != request.user: raise PermissionDenied
            context['allnighter'] = a
        except Allnighter.MultipleObjectsReturned: return HttpResponseBadRequest('')
        except Allnighter.DoesNotExist: raise Http404
        if request.method == 'POST':
            form = AllNighterForm(request.user, request.POST, instance = a)
        else:
            form = AllNighterForm(request.user, instance=a, initial={"date": a.date})
        context["date"] = a.date.strftime("%x")
    else: #we're creating a new allnighter
        if request.method == "POST":
            form = AllNighterForm(request.user, request.POST, instance = Allnighter(user=request.user))
        else:
            if "withdate" in request.GET:
                try:
                    defaultdate = datetime.datetime.strptime(request.GET["withdate"], "%Y%m%d").date()
                except:
                    defaultdate = prof.today()
            else:
                defaultdate = prof.today()
            form = AllNighterForm(request.user, initial={"date": str(defaultdate)})
    if request.method == "POST":
        if form.is_valid():
            if "delete" in form.data and form.data["delete"] == "on":
                if allNighter: a.delete()
                return HttpResponseRedirect('/mysleep/')
            new = form.save(commit=False)
            if allNighter == None:
                new.user = request.user
                new.save()
                form = AllNighterForm(request.user, instance=new)
                return HttpResponseRedirect('/sleep/allnighter/success/')
            else:
                new.save()
                return HttpResponseRedirect('/mysleep/')
    context['form']=form
    return render_to_response('editallnighter.html', context, context_instance=RequestContext(request))

@login_required
def editOrCreateSleep(request,sleep = None,success=False):
    context = {'success': success}
    if "from" in request.GET and request.GET["from"] == "partial": context["fromPartial"] = True
    prof = request.user.sleeperprofile
    defaulttz = prof.timezone
    if prof.use12HourTime: fmt = "%I:%M %p %x"
    else: fmt = "%H:%M %x"
    if sleep: # we're editing a sleep
        try:
            s = Sleep.objects.get(pk=sleep)
            if s.user != request.user: raise PermissionDenied
            context['sleep'] = s
        except Sleep.MultipleObjectsReturned:
            return HttpResponseBadRequest('')
        except Sleep.DoesNotExist:
            raise Http404
        if request.method == 'POST': form = SleepForm(request.user, fmt, request.POST, instance=s)
        else:
            initial = {
                    "start_time" : s.start_local_time().strftime(fmt),
                    "end_time" : s.end_local_time().strftime(fmt),
                    "date" : s.date.strftime("%x"),
                    }
            form = SleepForm(request.user, fmt, instance=s, initial=initial)
        context.update({"start": s.start_local_time().strftime(fmt), "end": s.end_local_time().strftime(fmt), "tz": s.timezone})
    else: # we're creating a new sleep
        if request.method == 'POST':
            form = SleepForm(request.user, fmt, request.POST, instance=Sleep(user=request.user))
        else:
            today = now().astimezone(pytz.timezone(defaulttz)).replace(hour=0,minute=0,second=0,microsecond=0)
            initial = {
                    "start_time" : today.strftime(fmt),
                    "end_time" : today.strftime(fmt),
                    "date" : today.date().strftime("%x"),
                    "timezone" : defaulttz,
                    }
            if "error" in request.GET:
                if request.GET["error"] == "partial":
                    context["partialError"] = True
                    try:
                        p = request.user.partialsleep
                        initial.update({"timezone": p.timezone, "start_time": p.start_local_time().strftime(fmt)})
                    except PartialSleep.DoesNotExist: pass
            form = SleepForm(request.user, fmt, initial=initial)
    if request.method == 'POST':
        if form.is_valid():
            if "delete" in form.data and form.data["delete"] == "on":
                if sleep: s.delete()
                return HttpResponseRedirect('/mysleep/')
            new = form.save(commit=False)
            if sleep == None:
                new.user = request.user
                new.save()
                form = SleepForm(request.user, fmt, instance=new)
                return HttpResponseRedirect('/sleep/simple/success/')
            else:
                new.save()
                return HttpResponseRedirect('/mysleep/')
    context['form']=form
    return render_to_response('editsleep.html', context, context_instance=RequestContext(request))

@login_required
def graph(request):
    return render_to_response('graph.html', {"user": request.user, "sleeps": request.user.sleep_set.all().order_by('-end_time')}, context_instance=RequestContext(request))

@login_required
def groups(request):
    context = {
            'groups' : request.user.sleepergroups.all(),
            'invites' : request.user.groupinvite_set.filter(accepted=None),
            }
    if request.method =="POST":
        form = GroupSearchForm(request.POST)
        if form.is_valid():
            gs=SleeperGroup.objects.filter(name__icontains=form.cleaned_data['group'], privacy__gte=SleeperGroup.REQUEST).exclude(members=request.user)
            context['results']=gs
            if gs.count() == 0 : context["noresults"] = True
    else:
        form = GroupSearchForm()
    context["form"] = form
    return render_to_response('groups.html', context, context_instance=RequestContext(request))

@login_required
def createGroup(request):
    if request.method == 'POST':
        form = GroupForm(request.POST)
        if form.is_valid():
            g=form.save()
            m=Membership(user=request.user,group=g,privacy=request.user.sleeperprofile.privacyLoggedIn, role=Membership.ADMIN)
            m.save()
            return HttpResponseRedirect('/groups/manage/%s/' % g.id)
    else:
        form=GroupForm()
    return render_to_response('create_group.html', {'form': form}, context_instance=RequestContext(request))

@login_required
def acceptInvite(request):
    if 'id' in request.POST and 'accepted' in request.POST:
        invites = GroupInvite.objects.filter(id=request.POST['id'],accepted=None)
        if len(invites)!=1:
            raise Http404
        invite = invites[0]
        if request.user.id is not invite.user_id:
            raise PermissionDenied
        if request.POST['accepted']=="True":
            invite.accept()
        else:
            invite.reject()
        return HttpResponse('')
    else:
        return HttpResponseBadRequest('')

@login_required
def inviteMember(request):
    if 'group' in request.POST and 'user' in request.POST:
        gid = request.POST['group']
        uid = request.POST['user']
        gs = SleeperGroup.objects.filter(id=gid)
        if len(gs)!=1 or request.user not in gs[0].members.all():
            raise Http404
        us = Sleeper.objects.filter(id=uid)
        if len(us)!=1:
            raise Http404
        g=gs[0]
        u=us[0]
        rs = GroupRequest.objects.filter(user = u, group = g, accepted=None)
        if rs.count() >= 1: #the user has made a request to join, accept them.
            r[0].accept()
        else:
            g.invite(u,request.user)
        return HttpResponse('')
    else:
        return HttpResponseBadRequest('')

@login_required
def manageMember(request):
    if 'group' in request.POST and 'user' in request.POST:
        gid = request.POST['group']
        uid = request.POST['user']
        gs = SleeperGroup.objects.filter(id=gid)
        if len(gs)!=1 or request.user not in gs[0].members.all():
            raise Http404
        us = Sleeper.objects.filter(id=uid)
        if len(us)!=1:
            raise Http404
        g=gs[0]
        u=us[0]
        if not (request.user == u):
            ms = Membership.objects.filter(user=request.user, group=g)
            if ms.count() != 1: raise Http404
            m = ms[0]
            if m.role < m.ADMIN: raise PermissionDenied
        if 'action' in request.POST and request.POST["action"] == "remove":
            for m in Membership.objects.filter(user=u,group=g):
                r = m.removeMember()
                if r == "redirect": return HttpResponseRedirect("/groups")
            return HttpResponse('')
        if 'action' in request.POST and request.POST["action"] == "makeAdmin":
            for m in Membership.objects.filter(user=u,group=g):
                m.makeAdmin()
            return HttpResponse('')
        if 'action' in request.POST and request.POST["action"] == "removeAdmin":
            for m in Membership.objects.filter(user=u, group=g):
                try:
                    m.makeMember()
                except ValueError:
                    return HttpResponseBadRequest('')
            return HttpResponse('')
    else:
        return HttpResponseBadRequest('')

@login_required
def groupRequest(request):
    if 'group' in request.POST:
        gid = request.POST['group']
        gs = SleeperGroup.objects.filter(id=gid)
        if gs.count() != 1: raise Http404
        g = gs[0]
        if g.privacy < SleeperGroup.REQUEST: raise PermissionDenied
        if g.privacy <= SleeperGroup.PUBLIC: # it's a public group, allow user to join
            m = Membership(user=request.user, group=g, privacy = request.user.sleeperprofile.privacyLoggedIn)
            m.save()
        invites = GroupInvites.objects.filter(user=request.user, group=g, accepted = None)
        if invites.count() >= 1: # the user has already been invited, accept them.
            invites[0].accept()
        g.request(request.user)
        return HttpResponse('')
    else:
        return HttpResponseBadRequest('')

@login_required
def groupJoin(request):
    if 'group' in request.POST:
        gid = request.POST['group']
        gs = SleeperGroup.objects.filter(id=gid)
        if gs.count() != 1: raise Http404
        g = gs[0]
        if g.privacy < SleeperGroup.PUBLIC: raise PermissionDenied
        m = Membership(user = request.user, group = g, privacy = request.user.sleeperprofile.privacyLoggedIn)
        m.save()
        return HttpResponse('')
    else:
        return HttpResponseBadRequest('')

@login_required
def processRequest(request):
    if 'id' in request.POST:
        rs = GroupRequest.objects.filter(id=request.POST["id"])
        if rs.count() != 1: raise 404
        r = rs[0]
        m = Membership.objects.get(group=r.group, user=request.user)
        if m.role < m.ADMIN: raise PermissionDenied
        if "accepted" in request.POST:
            if request.POST["accepted"] == "True":
                r.accept()
            elif request.POST["accepted"] == "False":
                r.reject()
            return HttpResponse('')
        return HttpResponseBadRequest('')
    else:
        return HttpResponseBadRequest('')

@login_required
def manageGroup(request,gid):
    gs=SleeperGroup.objects.filter(id=gid)
    if len(gs)!=1:
        raise Http404
    g=gs[0]
    if request.user not in g.members.all():
        raise PermissionDenied
    context={
            'group':g,
            'isAdmin': (request.user.membership_set.get(group = g).role >= 50),
            }
    if request.method == 'POST' and "SleeperSearchForm" in request.POST:
        searchForm=SleeperSearchForm(request.POST)
        if searchForm.is_valid():
            us=User.objects.filter(username__icontains=searchForm.cleaned_data['username']).exclude(sleepergroups__id=g.id)
            context['results']=us
            context['showResults'] = True
            context['count']=us.count()
    else:
        searchForm = SleeperSearchForm()
    if request.method == 'POST' and "GroupForm" in request.POST:
        if context['isAdmin'] == False:
            raise PermissionDenied
        groupForm = GroupForm(request.POST, instance=g)
        if groupForm.is_valid():
            if 'delete' in groupForm.data and groupForm.data['delete'] == 'on':
                g.delete()
                return HttpResponseRedirect('/groups/')
            groupForm.save()
        else:
            context['page'] = 2
    else:
        groupForm = GroupForm(instance=g)
    context['searchForm']=searchForm
    context['groupForm']=groupForm
    context['members']=g.members.all()
    if context['isAdmin']:
        context['requests'] = g.grouprequest_set.filter(accepted=None)
        if 'page' not in context and context['requests'].count() > 0: context['page'] = 3
    return render_to_response('manage_group.html',context,context_instance=RequestContext(request))

def leaderboard(request,group=None):
    if 'sort' not in request.GET or request.GET['sort'] not in ['zScore','avg','stDev', 'consistent', 'consistent2']:
        sortBy='zScore'
    else:
        sortBy=request.GET['sort']
    if group is None:
        lbSize=10
    else:
        gs = SleeperGroup.objects.filter(id=group)
        if gs.count()!=1:
            raise Http404
        group = gs[0]
        if request.user not in group.members.all():
            raise PermissionDenied
        nmembers = group.members.count()
        lbSize=nmembers if nmembers<4 else min(10,nmembers//2)
    ss = Sleeper.objects.sorted_sleepers(sortBy=sortBy,user=request.user,group=group)
    top = [ s for s in ss if s['rank']<=lbSize or request.user.is_authenticated() and s['user'].pk==request.user.pk ]
    n = now()
    recentWinner = Sleeper.objects.bestByTime(start=n-datetime.timedelta(3),end=n,user=request.user,group=group)[0]
    if group:
        allUsers = group.members.all()
    else:
        allUsers = Sleeper.objects.all()
    number = allUsers.filter(sleep__isnull=False).distinct().count()
    metricsToDisplay = ['zScore','avg','stDev','consistent','consistent2']
    metricsDisplayedAsTimes = ['zScore','zPScore','avg','avgSqrt','avgLog','avgRecip','stDev','posStDev','idealDev']
    context = {
            'group' : group,
            'top' : top,
            'recentWinner' : recentWinner,
            'total' : Sleep.objects.totalSleep(group=group),
            'number' : number,
            'leaderboard_valid' : len(ss),
            'metricsToDisplay' : metricsToDisplay,
            'metricsDisplayedAsTimes' : metricsDisplayedAsTimes
            }
    return render_to_response('leaderboard.html',context,context_instance=RequestContext(request))

def graphs(request,group=None):
    if group is not None:
        gs = SleeperGroup.objects.filter(id=group)
        if gs.count()!=1:
            raise Http404
        group = gs[0]
        if request.user not in group.members.all():
            raise PermissionDenied
    return render_to_response('graphs.html',{'group': group},context_instance=RequestContext(request))

def creep(request,username=None):
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
            followed = request.user.sleeperprofile.follows.order_by('username')
        total=creepable.distinct().count()
        if request.method == 'POST':
            form=SleeperSearchForm(request.POST)
            if form.is_valid():
                users = creepable.filter(username__icontains=form.cleaned_data['username']).distinct()
                count = users.count()
                if count==1: return HttpResponseRedirect('/creep/%s/' % users[0].username)
                else:
                    context = {
                            'results' : users,
                            'count' : count,
                            'form' : form,
                            'new' : False,
                            'total' : total,
                            'followed' : followed,
                            }
                    return render_to_response('creepsearch.html',context,context_instance=RequestContext(request))
        else:
            form = SleeperSearchForm()
        context = {
                'form' : form,
                'new' : True,
                'total' : total,
                'followed' : followed,
                }
        return render_to_response('creepsearch.html',context,context_instance=RequestContext(request))
    else:
        context = {}
        try:
            user=Sleeper.objects.get(username=username)
            p = user.sleeperprofile
            if p.user_id == request.user.id and "as" in request.GET:
                priv = p.getPermissions(request.GET['as'])
            else:
                priv = p.getPermissions(request.user)
            if not(request.user.is_anonymous()) and request.user.pk == user.pk: context["isself"] =True
            if priv<=p.PRIVACY_NORMAL: return render_to_response('creepfailed.html',{},context_instance=RequestContext(request))
        except:
            return render_to_response('creepfailed.html',{},context_instance=RequestContext(request))
        context.update({'user' : user,'global' : user.decayStats()})
        if priv>=p.PRIVACY_PUBLIC: context['sleeps']=user.sleep_set.all().order_by('-end_time')
        if priv>=p.PRIVACY_GRAPHS:
            if "type" in request.GET and request.GET["type"] == "graph": return render_to_response('graph.html',context,context_instance=RequestContext(request))
            context["graphs"] = True
        return render_to_response('creep.html',context,context_instance=RequestContext(request))

@login_required
def editProfile(request):
    p = request.user.sleeperprofile
    if p.use12HourTime: fmt = "%I:%M %p"
    else: fmt = "%H:%M"
    if request.method == 'POST':
        form = SleeperProfileForm(fmt, request.POST, instance=p)
        context = {"form":form}
        if form.is_valid():
            form.save()
            return HttpResponseRedirect('/editprofile/?success=True')
        else:
            for k in form.errors.viewkeys():
                if "ideal" in k:
                    context["page"] = 2
                    break
    else:
        initial = {"idealWakeupWeekend": p.idealWakeupWeekend.strftime(fmt),
                "idealWakeupWeekday": p.idealWakeupWeekday.strftime(fmt),
                "idealSleepTimeWeekend": p.idealSleepTimeWeekend.strftime(fmt),
                "idealSleepTimeWeekday": p.idealSleepTimeWeekday.strftime(fmt),}
        form = SleeperProfileForm(fmt, instance=p, initial = initial)
        context = {"form":form}
        if "success" in request.GET and request.GET["success"] == "True": context["success"] = True
    return render_to_response('editprofile.html', context ,context_instance=RequestContext(request))

@login_required
def exportSleeps(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="zscore_sleeps_' + request.user.username + '.csv"'
    
    writer = csv.writer(response)
    writer.writerow(["Start Time", "End Time", "Date", "Comments", "Timezone", "Quality"])

    for s in request.user.sleep_set.all():
        writer.writerow([s.start_local_time(), s.end_local_time(), s.date, s.comments, s.timezone, s.quality])

    return response

@login_required
def friends(request):
    prof = request.user.sleeperprofile
    friendfollow = (prof.friends.all() | prof.follows.all()).distinct().order_by('username').select_related('sleeperprofile').prefetch_related('sleeperprofile__friends')
    requests = request.user.requests.filter(friendrequest__accepted=None).order_by('user__username')
    if request.method == 'POST':
        form=SleeperSearchForm(request.POST)
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
            return render_to_response('friends.html',context,context_instance=RequestContext(request))
    else:
        form = SleeperSearchForm()
    context = {
            'form' : form,
            'new' : True,
            'friendfollow' : friendfollow,
            'requests' : requests,
            }
    return render_to_response('friends.html',context,context_instance=RequestContext(request))
            
@login_required
def requestFriend(request):
    if 'id' in request.POST:
        i = request.POST['id']
        if i==request.user.pk or len(User.objects.filter(pk=i))!=1:
            raise Http404
        them = Sleeper.objects.get(pk=i)
        if not FriendRequest.objects.filter(requestor=request.user.sleeperprofile,requestee=them):
            if request.user in them.sleeperprofile.friends.all():
                accept = True
            else:
                accept = None
            FriendRequest.objects.create(requestor=request.user.sleeperprofile,requestee=them,accepted=accept)
        return HttpResponse('')
    else:
        return HttpResponseBadRequest('')

@login_required
def hideRequest(request):
    if 'id' in request.POST:
        i = request.POST['id']
        if i==request.user.pk or len(User.objects.filter(pk=i))!=1:
            raise Http404
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
            raise Http404
        prof = request.user.sleeperprofile
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
            raise Http404
        prof = request.user.sleeperprofile
        prof.friends.remove(i)
        return HttpResponse('')
    else:
        return HttpResponseBadRequest('')

@login_required
def follow(request):
    if 'id' in request.POST:
        i = request.POST['id']
        if i==request.user.pk or len(User.objects.filter(pk=i))!=1:
            raise Http404
        prof = request.user.sleeperprofile
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
            raise Http404
        prof = request.user.sleeperprofile
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
    if start > end: start,end = end, start #if end is after start, flip them
    s = Sleep(user=request.user, start_time=start, end_time=end, comments=comments, date=date,timezone=timezone)
    try:
        s.validate_unique()
        s.save()
    except ValidationError:
        return HttpResponseBadRequest('')
    return HttpResponse('')

@login_required
def createPartialSleep(request):
    prof = request.user.sleeperprofile
    timezone = prof.timezone
    start = now().astimezone(pytz.timezone(timezone)).replace(microsecond = 0) + prof.getPunchInDelay()
    try:
        p = PartialSleep(user = request.user, start_time = start,timezone = timezone)
        p.save()
        if "next" in request.GET: return HttpResponseRedirect(request.GET["next"])
        return HttpResponseRedirect("/")
    except IntegrityError:
        return HttpResponseBadRequest('')

@login_required
def finishPartialSleep(request):
    timezone = request.user.sleeperprofile.timezone
    pytztimezone = pytz.timezone(timezone)
    try:
        p = request.user.partialsleep
        start = p.start_time.astimezone(pytztimezone)
        end = now().astimezone(pytz.timezone(timezone)).replace(microsecond = 0)
        date = end.date()
        s = Sleep(user = request.user, start_time = start, end_time = end, date = date, timezone = timezone, comments = "")
        try:
            s.validate_unique()
            s.save()
            p.delete()
            return HttpResponseRedirect("/sleep/edit/" + str(s.pk) + "/?from=partial")
        except ValidationError:
            return HttpResponseRedirect("/sleep/simple/?error=partial")
    except PartialSleep.DoesNotExist:
        return HttpResponseBadRequest('')

@login_required
def deletePartialSleep(request):
    try:
        p= request.user.partialsleep
        p.delete()
        if "next" in request.GET: return HttpResponseRedirect(request.GET["next"])
        return HttpResponseRedirect("/")
    except PartialSleep.DoesNotExist:
        return HttpResponseBadRequest('')

@login_required
def deleteSleep(request):
    if 'id' in request.POST:
        i = request.POST['id']
        s = Sleep.objects.filter(pk=i)
        if len(s) == 0:
            raise Http404
        s = s[0]
        if s.user != request.user:
            raise PermissionDenied
        s.delete()
        return HttpResponse('')
    return HttpResponseBadRequest('')

@login_required
def deleteAllnighter(request):
    if 'id' in request.POST:
        i = request.POST['id']
        a = Allnighter.objects.filter(pk=i)
        if len(a) == 0: raise Http404
        a = a[0]
        if a.user != request.user: raise PermissionDenied
        a.delete()
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

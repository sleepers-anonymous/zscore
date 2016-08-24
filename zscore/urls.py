from django.conf.urls import include, url
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.views.generic.base import TemplateView, RedirectView
from django.contrib.auth.decorators import login_required

import users.views
import zscore.views
import sleep.views

urlpatterns = [
    # Examples:
    # url(r'^$', zscore.views.home, name='home'),
    # url(r'^zscore/', include('zscore.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Admin panel:
    url(r'^admin/', admin.site.urls),

    # Login
    url(r'^accounts/login/submit/$', auth_views.login),
    url(r'^accounts/login/$', auth_views.login, {
            'template_name': 'users/login.html'
    }),
    url(r'^accounts/logout/$', auth_views.logout, {
            'template_name': 'users/logout.html'
    }),
    url(r'^accounts/create/$', users.views.CreateUser.as_view()),
    url(r'^accounts/profile/$', RedirectView.as_view(url='/mysleep')),
    url(r'^accounts/password/reset/$', auth_views.password_reset, {
            'template_name': 'users/password_reset_form.html',
            'email_template_name': 'users/password_reset_email.html',
            'post_reset_redirect': '/accounts/password/reset/done/'
    }),
    url(r'^accounts/password/reset/done/$', auth_views.password_reset_done, {
            'template_name': 'users/password_reset_done.html',
    }),
    url(r'^accounts/password/reset/(?P<uidb64>[0-9A-Za-z]+)-(?P<token>.+)/$', auth_views.password_reset_confirm, {
            'template_name': 'users/password_reset_confirm.html',
            'post_reset_redirect': '/accounts/password/done/'
    }),
    url(r'^accounts/password/done/$', auth_views.password_reset_complete, {
            'template_name': 'users/password_reset_complete.html'
    }),

    # Pages
    url(r'^leaderboard/$', sleep.views.leaderboard),
    url(r'^leaderboard/(\d+)/$', sleep.views.leaderboard),
    url(r'^graphs/$', sleep.views.graphs),
    url(r'^graphs/(\d+)/$', sleep.views.graphs),
    url(r'^mysleep/$', login_required(TemplateView.as_view(
        template_name='sleep/mysleep.html'))),
    url(r'^sleep/simple/$', sleep.views.editOrCreateSleep),
    url(r'^sleep/simple/success/$', sleep.views.editOrCreateSleep, {'success' : True}),
    url(r'^sleep/allnighter/$', sleep.views.editOrCreateAllnighter),
    url(r'^sleep/allnighter/success/$', sleep.views.editOrCreateAllnighter, {'success' : True}),
    url(r'^mygraphs/$', sleep.views.graph),
    url(r'^editprofile/$', sleep.views.editProfile),
    url(r'^creep/$', sleep.views.creep),
    url(r'^creep/([^/]*)/$', sleep.views.creep),
    url(r'^groups/$', sleep.views.groups),
    url(r'^groups/create/$', sleep.views.CreateGroup.as_view()),
    url(r'^groups/invite/$', sleep.views.inviteMember),
    url(r'^groups/accept/$', sleep.views.acceptInvite),
    url(r'^groups/membership/$', sleep.views.manageMember),
    url(r'^groups/manage/(\d+)/$',sleep.views.manageGroup),
    url(r'^groups/request/$', sleep.views.groupRequest),
    url(r'^groups/request/process/$', sleep.views.processRequest),
    url(r'^groups/join/$', sleep.views.groupJoin),
    url(r'^friends/$', sleep.views.friends),
    url(r'^friends/request/$', sleep.views.requestFriend),
    url(r'^friends/hide/$', sleep.views.hideRequest),
    url(r'^friends/add/$', sleep.views.addFriend),
    url(r'^friends/remove/$', sleep.views.removeFriend),
    url(r'^friends/follow/$', sleep.views.follow),
    url(r'^friends/unfollow/$', sleep.views.unfollow),
    url(r'^sleep/getSleeps/$', sleep.views.getSleepsJSON),
    url(r'^sleep/create/$', sleep.views.createSleep),
    url(r'^sleep/delete/$', sleep.views.deleteSleep),
    url(r'^sleep/createPartial/$', sleep.views.createPartialSleep),
    url(r'^sleep/finishPartial/$', sleep.views.finishPartialSleep),
    url(r'^sleep/deletePartial/$', sleep.views.deletePartialSleep),
    url(r'^sleep/delete/allnighter/$', sleep.views.deleteAllnighter),
    url(r'^sleep/edit/(?P<sleep>\d+)/', sleep.views.editOrCreateSleep),
    url(r'^sleep/editallnighter/(?P<allNighter>\d+)/', sleep.views.editOrCreateAllnighter),
    url(r'^$', sleep.views.home),
    url(r'^faq/$', TemplateView.as_view(template_name='faq.html')),
    url(r'^privacy/$', TemplateView.as_view(template_name='privacy.html')),
    url(r'^sleep/export/$', sleep.views.exportSleeps),
]

from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'zscore.views.home', name='home'),
    # url(r'^zscore/', include('zscore.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Admin panel:
    url(r'^admin/', include(admin.site.urls)),

    # Login
    url(r'^accounts/login/submit/$', 'django.contrib.auth.views.login'),
    url(r'^accounts/login/$', 'django.contrib.auth.views.login', {
            'template_name': 'users/login.html'
    }),
    url(r'^accounts/logout/$', 'django.contrib.auth.views.logout', {
            'template_name': 'users/logout.html'
    }),
    url(r'^accounts/create/$', 'users.views.create'),
    url(r'^accounts/profile/$', 'users.views.profile'),
    url(r'^accounts/password/reset/$', 'django.contrib.auth.views.password_reset', {
            'template_name': 'users/password_reset_form.html',
            'email_template_name': 'users/password_reset_email.html',
            'post_reset_redirect': '/accounts/password/reset/done/'
    }),
    url(r'^accounts/password/reset/done/$', 'django.contrib.auth.views.password_reset_done', {
            'template_name': 'users/password_reset_done.html',
    }),
    url(r'^accounts/password/reset/(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)/$', 'django.contrib.auth.views.password_reset_confirm', {
            'template_name': 'users/password_reset_confirm.html',
            'post_reset_redirect': '/accounts/password/done/'
    }),
    url(r'^accounts/password/done/$', 'django.contrib.auth.views.password_reset_complete', {
            'template_name': 'users/password_reset_complete.html'
    }),

    # Pages
    url(r'^leaderboard/$', 'sleep.views.leaderboard'),
    url(r'^leaderboard/(\w+)/$', 'sleep.views.leaderboard'),
    url(r'^mysleep/$', 'sleep.views.mysleep'),
    url(r'^editprofile/$', 'sleep.views.editProfile'),
    url(r'^creep/$', 'sleep.views.creep'),
    url(r'^creep/([^/]*)/$', 'sleep.views.creep'),
    url(r'^creep/([^/]*)/([^/]*)/$', 'sleep.views.creep'),
    url(r'^friends/$', 'sleep.views.friends'),
    url(r'^friends/add/$', 'sleep.views.addFriend'),
    url(r'^friends/remove/$', 'sleep.views.removeFriend'),
    url(r'^friends/follow/$', 'sleep.views.follow'),
    url(r'^friends/unfollow/$', 'sleep.views.unfollow'),
    url(r'^sleep/getSleeps/$', 'sleep.views.getSleepsJSON'),
    url(r'^sleep/create/$', 'sleep.views.createSleep'),
    url(r'^sleep/delete/$', 'sleep.views.deleteSleep'),
    url(r'^sleep/edit/(?P<sleep>\d+)/', 'sleep.views.editSleep'),
    url(r'^$', 'sleep.views.home'),
    url(r'^faq/$', 'sleep.views.faq'),
)

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
            'template_name': 'login.html'
    }),
    url(r'^accounts/logout/$', 'django.contrib.auth.views.logout', {
            'template_name': 'logout.html'
    }),

    # Pages
    url(r'^leaderboard/$', 'sleep.views.leaderboard'),
    url(r'^mysleep/$', 'sleep.views.mysleep'),
    url(r'^sleep/submit/$', 'sleep.views.submitSleep'),
    url(r'^sleep/delete/$', 'sleep.views.deleteSleep'),
    url(r'^$', 'sleep.views.home'),
)

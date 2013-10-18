from django.contrib import admin
from metrics.models import *

class MetricsProfileAdmin(admin.ModelAdmin):
    list_display = ('user',)
    search_fields = ('user__username',)

class MetricsCategoryAdmin(admin.ModelAdmin):
    list_display = ('name','creator','metrictype')
    list_filter = ('creator',)
    ordering = ('creator__username','name')

class MetricsInstanceAdmin(admin.ModelAdmin):
    list_display = ('user', 'category', 'time', 'value')
    list_filter = ('user', 'category', 'time')
    ordering = ('user__username', '-time')

admin.site.register(MetricsProfile, MetricsProfileAdmin)
admin.site.register(MetricsCategory, MetricsCategoryAdmin)
admin.site.register(MetricsInstance, MetricsInstanceAdmin)

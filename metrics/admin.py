from django.contrib import admin
from metrics.models import *

class MetricsProfileAdmin(admin.ModelAdmin):
    list_display = ('user',)
    search_fields = ('user__username',)

class MetricsCategoryAdmin(admin.ModelAdmin):
    list_display = ('name','creator','metrictype')
    list_filter = ('creator',)
    ordering = ('creator__username','name')

class SingleMetricInline(admin.TabularInline):
    model=SingleMetricsInstance

class MetricsInstanceAdmin(admin.ModelAdmin):
    list_display = ('user', 'time',)
    list_filter = ('user', 'time')
    ordering = ('user__username', '-time')
    inlines = [SingleMetricInline]

class SingleMetricsInstanceAdmin(admin.ModelAdmin):
    list_display = ('instance','category')
    list_filter = ('category',)

admin.site.register(MetricsProfile, MetricsProfileAdmin)
admin.site.register(MetricsCategory, MetricsCategoryAdmin)
admin.site.register(MetricsInstance, MetricsInstanceAdmin)
admin.site.register(SingleMetricsInstance, SingleMetricsInstanceAdmin)

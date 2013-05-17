from django import template
register = template.Library()

# Inclusion tags
@register.inclusion_tag('inclusion/stats.html')
def statsView():
    # Return an empty context for now
    return {}
@register.inclusion_tag('inclusion/sleep_list.html')
def sleepListView():
    # Return an empty context for now
    return {}
@register.inclusion_tag('inclusion/sleep_entry.html')
def sleepEntryView():
    # No context needed
    return {}

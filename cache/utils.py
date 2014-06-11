from django.core import cache

def expireTemplateCache(fragment_name, *variables):
    # At this point you should probably just call
    # django.core.cache.utils.make_template_fragment_key directly, but for
    # compatibility we include the following convenience method.
    key = cache.utils.make_template_fragment_key(fragment_name, variables)
    cache.cache.delete(key)

def authStatus(user):
    if 'is_authenticated' in dir(user):
        return user.is_authenticated()
    else:
        return str(user)

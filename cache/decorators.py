import functools

from django.core.cache import cache

def cache_function(cacheKeyGenerator,groupKeyGenerator=None):
    def _dec(func):
        def _wrapped(*args,**kwargs):
            keyParts = cacheKeyGenerator(*args,**kwargs) if '__call__' in dir(cacheKeyGenerator) else cacheKeyGenerator
            groupKeyParts = groupKeyGenerator(*args,**kwargs) if '__call__' in dir(groupKeyGenerator) else groupKeyGenerator
            if keyParts is not None and groupKeyParts is not None: #if we want to set this up as part of a cache group
                cacheKey = func.__name__ + ":" + ":".join(map(str,keyParts))
                groupKey = func.__name__ + ":" + ":".join(map(str,groupKeyParts))
                cacheGroup = cache.get(groupKey,set())
                if cacheKey in cacheGroup:
                    cached = cache.get(cacheKey)
                    if cached is not None:
                        return cached
                answer = func(*args,**kwargs)
                cache.set(cacheKey,answer)
                cacheGroup = cache.get(groupKey,set())
                cacheGroup.add(cacheKey)
                cache.set(groupKey,cacheGroup)
                return answer
            elif keyParts is not None:
                cacheKey = func.__name__ + ":" + ":".join(map(str,keyParts))
                cached = cache.get(cacheKey)
                if cached is not None:
                    return cached
                answer = func(*args,**kwargs)
                cache.set(cacheKey,answer)
                return answer
            else:
                return func(*args,**kwargs)
        return functools.update_wrapper(_wrapped,func)
    return _dec



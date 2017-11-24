import threading

from django.core.cache.backends import memcached


class GAEMemcacheBackend(memcached.BaseMemcachedCache):
    def __init__(self, server, params):
        from google.appengine.api import memcache
        super(GAEMemcacheBackend, self).__init__(
            server, params, library=memcache, value_not_found_exception=None)
        self._client = threading.local()

    @property
    def _cache(self):
        if getattr(self._client, 'client', None) is None:
            self._client.client = self._lib.Client()
        return self._client.client

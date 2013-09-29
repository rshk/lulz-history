##=============================================================================
## Copyright 2013 Samuele Santi
##
## Licensed under the Apache License, Version 2.0 (the "License");
## you may not use this file except in compliance with the License.
## You may obtain a copy of the License at
##
##     http://www.apache.org/licenses/LICENSE-2.0
##
## Unless required by applicable law or agreed to in writing, software
## distributed under the License is distributed on an "AS IS" BASIS,
## WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
## See the License for the specific language governing permissions and
## limitations under the License.
##=============================================================================

"""
Miscellaneous utilities
"""

from functools import wraps


def cached(cache, timeout=5 * 60, key=None):
    """
    Decorator for caching function return values.

    :param cache:
        The cache object to be used for caching

    :param timeout:
        The cache timeout, in seconds

    :param key:
        The key to be used for caching this functions's
        return value.
        If it's a callable, it will be called with the
        args/kwargs of the wrapped function; else, its
        ``.format()`` method will be called passing
        args and kwargs (assuming it's a format string..)

    :return:
        A decorator to be applied to the function to be
        cached
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            ## Figure out the cache key
            if hasattr(key, '__call__'):
                cache_key = key(*args, **kwargs)
            elif key is not None:
                cache_key = key.format(*args, **kwargs)
            else:
                ## We might want to generate from args,
                ## but it's risky and we want people to be
                ## explicit about which key to use..
                raise ValueError("Unspecified cache key")

            ## First, try getting from cache
            rv = cache.get(cache_key)
            if rv is not None:
                return rv

            ## Not found, we need to run the actual function
            rv = f(*args, **kwargs)
            cache.set(cache_key, rv, timeout=timeout)
            return rv

        return decorated_function
    return decorator

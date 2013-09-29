"""
Test for the utility functions used in the project
"""

import time

import pytest
import mock


def test_function_cache():
    ## test the @cached decorator used in the views

    from werkzeug.contrib.cache import SimpleCache
    from functools import partial
    from LulzHistory.utils import cached as cached_decorator
    cache = SimpleCache(default_timeout=120)
    cached = partial(cached_decorator, cache)

    calls = {'myfunc': 0}

    @cached(30, 'myfunc/{0}')
    def myfunc(arg):
        calls['myfunc'] += 1
        if 0 <= arg <= 5:
            return "Retval #{0}".format(arg)
        raise ValueError("Invalid argument")

    assert myfunc(0) == 'Retval #0'
    assert calls['myfunc'] == 1
    assert myfunc(1) == 'Retval #1'
    assert calls['myfunc'] == 2
    assert myfunc(2) == 'Retval #2'
    assert calls['myfunc'] == 3

    assert myfunc(1) == 'Retval #1'  # Should *not* call myfunc
    assert calls['myfunc'] == 3

    ## Exceptions should pass through directly
    with pytest.raises(Exception):
        myfunc(200)
    assert calls['myfunc'] == 4

    ## Exceptions are not cached
    with pytest.raises(Exception):
        myfunc(200)
    assert calls['myfunc'] == 5

    assert myfunc(2) == 'Retval #2'  # Should *not* call myfunc
    assert calls['myfunc'] == 5

    assert myfunc(3) == 'Retval #3'
    assert calls['myfunc'] == 6

    ## Test cache expiration.
    ##----------------------------------------
    ## We use mock to fake the date returned by the time.time()
    ## imported in werkzeug.contrib.cache

    now = time.time()

    def fake_date(delta=0):
        return mock.patch(
            'werkzeug.contrib.cache.time',
            return_value=(now + delta))

    with fake_date(0):
        myfunc(4)
        assert calls['myfunc'] == 7

    with fake_date(10):
        myfunc(4)
        assert calls['myfunc'] == 7

    with fake_date(60):
        myfunc(4)
        assert calls['myfunc'] == 8


def test_image_filename_match():
    from LulzHistory.views import img_file_re
    should_match = [
        'a0b1c2d3e4.jpg',
        '0123456789abcdef0123456789abcdef01234567.jpg',
        'a0b1c2d3e4.gif',
        '0123456789abcdef0123456789abcdef01234567.gif',
        'a0b1c2d3e4.png',
        '0123456789abcdef0123456789abcdef01234567.png',
    ]
    should_not_match = [
        'this-contains-invalid-characters.jpg',
        'a0123.jpg',
        'aaa.gif',
        '123.png',
        'a0-12-b3.jpg',
        '0123456789abcdef',
        '0123456789abcdef.jpg.exe',
        '_abc123def456.jpg'
        '0123456789abcdef0123456789abcdef0123456789abcdef.jpg',
        'A0B1C2D3E4.jpg',
    ]
    for filename in should_match:
        assert img_file_re.match(filename)
    for filename in should_not_match:
        assert not img_file_re.match(filename)

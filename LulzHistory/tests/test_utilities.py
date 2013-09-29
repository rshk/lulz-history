"""
Test for the utility functions used in the project
"""

import pytest


def test_function_cache():
    ## todo: test the @cached decorator used in the views
    from werkzeug.contrib.cache import SimpleCache
    from functools import partial
    from LulzHistory.utils import cached as cached_decorator
    cache = SimpleCache(default_timeout=120)
    cached = partial(cached_decorator, cache)

    @cached(30, 'myfunc/{0}')
    def myfunc(arg):
        if 0 <= arg <= 5:
            return "Retval #{0}".format(arg)
        raise ValueError("Invalid argument")

    assert myfunc(0) == 'Retval #0'
    assert myfunc(1) == 'Retval #1'
    assert myfunc(2) == 'Retval #2'
    assert myfunc(1) == 'Retval #1'  # Should *not* call myfunc
    with pytest.raises(Exception):
        myfunc(200)
    assert myfunc(2) == 'Retval #2'  # Should *not* call myfunc
    assert myfunc(3) == 'Retval #3'


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

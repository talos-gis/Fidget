from typing import Callable, Any

from functools import wraps


def throwaway_cache(func: Callable[[], Any]):
    has_value = False
    value = None

    @wraps(func)
    def ret():
        nonlocal value, has_value
        if not has_value:
            value = func()
            has_value = True
        return value

    return ret


def error_details(e: Exception):
    ret = []
    while e:
        ret.append(f'{type(e).__name__}: {e}')
        e = e.__cause__
    return '\nfrom:\n'.join(ret)

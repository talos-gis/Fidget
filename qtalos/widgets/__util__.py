from functools import wraps


def rename(new_name):
    def ret(func):
        @wraps(func)
        def ret(*args, **kwargs):
            return func(*args, **kwargs)

        ret.__name__ = new_name
        return ret

    return ret

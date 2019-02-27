from functools import wraps


def rename(new_name):
    def ret(func):
        @wraps(func)
        def ret(*args, **kwargs):
            return func(*args, **kwargs)

        ret.__name__ = new_name
        return ret

    return ret


def has_init(cls):
    return '__init__' in cls.__dict__


def is_trivial_printer(p):
    return p in (str, repr)

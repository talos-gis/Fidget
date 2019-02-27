from functools import partial


def inner_widget(*args, **kwargs):
    def ret(cls):
        cls.__is_inner__ = partial(cls, *args, **kwargs)
        return cls

    return ret


def get_idiomatic_inner_widgets(cls):
    for v in cls.__dict__.values():
        i = getattr(v, '__is_inner__', False)
        if i:
            yield i

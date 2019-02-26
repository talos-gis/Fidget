from qtalos.value_widget import ParseError, ValidationError
from qtalos.__util__ import exc_wrap

wrap_parser = exc_wrap(ParseError('converter function raised an inner exception'))
wrap_validator = exc_wrap(ValidationError('converter function raised an inner exception'))


def validator(message=..., func=None):
    def ret(func):
        nonlocal message
        if message is ...:
            message = func.__doc__

        def ret(v):
            if not func(v):
                raise ValidationError(message)

        return ret

    if func:
        return ret(func)
    return ret

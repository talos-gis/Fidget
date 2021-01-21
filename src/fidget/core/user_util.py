from fidget.core.fidget_value import ParseError, ValidationError
from fidget.core.__util__ import exc_wrap

wrap_parser = exc_wrap(ParseError)
wrap_validator = exc_wrap(ValidationError)

def validator(message=..., func=None):
    """
    wrap a function so it throws a ValidationError if it returns False
    :param message: the message to set the error to. default is to use the function's __doc__
    :param func: the function to wrap. can be used as a decorator
    :return: a validator function
    """
    def ret(func):
        nonlocal message
        if message is ...:
            message = func.__doc__

        def ret(v):
            ret = func(v)
            if not ret:
                raise ValidationError(message)
            return ret

        return ret

    if func:
        return ret(func)
    return ret

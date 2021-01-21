from typing import TypeVar, Generic, Iterable

from fidget.core import Fidget, FidgetTemplate

"""
Idiomatic inner widgets are ValidWidget classes defined with the inner_widget decorator inside of wrapper ValidWidget
classes. If an inner widget is defined, it's template becomes the default inner template of the class.
"""


def inner_fidget(*args, **kwargs):
    """
    define a ValidWidget class as an idiomatic inner widget
    :param args: arguments forwarded to the template
    :param kwargs:  arguments forwarded to the template
    """

    def ret(cls):
        cls.__is_inner__ = cls.template(*args, **kwargs)
        return cls

    return ret


def get_idiomatic_inner_template(cls):
    """
    get all the idiomatic inner fidget templates defined in a class
    """
    for v in cls.__dict__.values():
        i = getattr(v, '__is_inner__', False)
        if i:
            yield i


T = TypeVar('T')
I = TypeVar('I')


class SingleFidgetWrapper(Generic[I, T], Fidget[T]):
    """
    A superclass for wrapping a single template
    """

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        idiomatic_inners = get_idiomatic_inner_template(cls)
        try:
            inner_template = next(idiomatic_inners)
        except StopIteration:
            inner_template = None
        else:
            if cls.INNER_TEMPLATE:
                raise Exception('cannot define idiomatic inner template inside a class with an INNER_TEMPLATE')

            try:
                _ = next(idiomatic_inners)
            except StopIteration:
                pass
            else:
                raise Exception(f'{cls.__name__} can only have 1 idiomatic inner template')

        if inner_template:
            cls.INNER_TEMPLATE = inner_template

    def indication_changed(self, value):
        super().indication_changed(value)
        self.inner.indication_changed(value)

    INNER_TEMPLATE: FidgetTemplate[I]


@SingleFidgetWrapper.template_class
class SingleFidgetWrapperTemplate(FidgetTemplate):
    """
    A template that forwards its title from its first parameter
    """
    @property
    def title(self):
        it = self._inner_template()
        if it:
            return it.title
        return super().title

    def _inner_template(self):
        if self.widget_cls.INNER_TEMPLATE:
            return self.widget_cls.INNER_TEMPLATE
        if self.args:
            return self.args[0].template_of()
        return None


class MultiFidgetWrapper(Generic[I, T], Fidget[T]):
    """
    A superclass for wrapping multiple templates
    """

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        idiomatic_inners = list(get_idiomatic_inner_template(cls))
        if idiomatic_inners:
            if cls.INNER_TEMPLATES:
                raise Exception('cannot define idiomatic inner templates inside a class with an INNER_TEMPLATES')

            cls.INNER_TEMPLATES = idiomatic_inners

    INNER_TEMPLATES: Iterable[FidgetTemplate[I]]

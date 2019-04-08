from __future__ import annotations

from typing import Iterable, Generic, TypeVar, Collection, Any

from abc import abstractmethod

from fidget.core.plaintext_adapter import high_priority

from fidget.core import ParseError, ValidationError, inner_plaintext_parser, inner_plaintext_printer, \
    FidgetTemplate, explicit, json_parser, TemplateLike, json_printer

from fidget.widgets.idiomatic_inner import MultiFidgetWrapper
from fidget.widgets.__util__ import only_valid

T = TypeVar('T', bound=Iterable)


class FidgetCompound(Generic[T], MultiFidgetWrapper[Any, T]):
    def __init__(self, title, inner_templates: Iterable[TemplateLike] = None, **kwargs):
        inner_templates = self._make_inner_templates(
            only_valid(inner_templates=inner_templates, INNER_TEMPLATES=self.INNER_TEMPLATES, _self=self)
        )

        FidgetTemplate.extract_default(*self.inner_templates_values(inner_templates), sink=kwargs, upper_space=type(self))

        super().__init__(title, **kwargs)

        self.inner_templates = inner_templates

        self.inners = None

    INNER_TEMPLATES: Iterable[TemplateLike] = None

    @classmethod
    @abstractmethod
    def _make_inner_templates(cls, inner_templates_param: Iterable[TemplateLike]):
        pass

    @classmethod
    @abstractmethod
    def inner_templates_values(cls, inner_templates):
        pass

    @classmethod
    @abstractmethod
    def _make_inners(cls, inner_templates):
        pass

    @classmethod
    def inners_values(cls, inners):
        return (v for (k, v) in cls.inners_items(inners))

    @classmethod
    @abstractmethod
    def inners_items(cls, inners):
        pass

    @classmethod
    @abstractmethod
    def init_result(cls):
        pass

    @classmethod
    @abstractmethod
    def insert_result(cls, res, key, value):
        pass

    @classmethod
    @abstractmethod
    def result_zip_subwidget(cls, res, inners):
        pass

    def make_inners(self):
        assert self.inners is None, 'inners is already constructed!'

        self.inners = self._make_inners(self.inner_templates)

        if not self.inners:
            raise ValueError('at least one inner fidget must be provided')

        for inner in self.inners_values(self.inners):
            inner.on_change.connect(self.change_value)

        self.setFocusProxy(
            next(iter(self.inners_values(self.inners)))
        )

        return self.inners

    def parse(self):
        d = self.init_result()
        for key, subwidget in self.inners_items(self.inners):
            try:
                value = subwidget.maybe_parse()
            except ParseError as e:
                raise ParseError('error parsing ' + subwidget.title, offender=subwidget) from e
            self.insert_result(d, key, value)
        return d

    def validate(self, d):
        super().validate(d)
        for (k, v), subwidget in self.result_zip_subwidget(d, self.inners):
            try:
                subwidget.maybe_validate(v)
            except ValidationError as e:
                raise ValidationError('error validating ' + subwidget.title, offender=subwidget) from e

    @abstractmethod
    def _from_json(self, json_obj, exact=True):
        pass

    @abstractmethod
    def _to_json(self, state):
        pass

    @inner_plaintext_parser
    @json_parser()
    def from_json(self, d, exact=True):
        return self._from_json(d, exact=exact)

    @explicit
    @inner_plaintext_parser
    @json_parser()
    def from_json_wildcard(self, v):
        return self._from_json(v, exact=False)

    @inner_plaintext_printer
    @high_priority
    @json_printer
    def to_json(self, d):
        return self._to_json(d)

    def _fill(self, res):
        for (k, v), subwidget in self.result_zip_subwidget(res, self.inners):
            subwidget.fill(v)

    @property
    def fill(self):
        if not all(sw.fill for sw in self.inners_values(self.inners)):
            return None
        return self._fill

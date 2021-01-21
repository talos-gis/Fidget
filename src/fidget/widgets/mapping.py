from __future__ import annotations

from typing import Union, Mapping, Iterable, Tuple, TypeVar, Any

from fidget.core import PlaintextPrintError, PlaintextParseError, FidgetTemplate, TemplateLike

from fidget.widgets.compound import FidgetCompound

T = TypeVar('T')
NamedTemplate = Union[
    TemplateLike[T], Tuple[str, TemplateLike[T]]
]


class FidgetMapping(FidgetCompound[Mapping]):
    def __init__(self, title, inner_templates: Iterable[NamedTemplate] = None, **kwargs):
        super().__init__(title, inner_templates, **kwargs)

    INNER_TEMPLATES: Iterable[NamedTemplate] = None

    def _make_inner_templates(self, inner_templates_param: Iterable[TemplateLike]):
        return dict(
            self._to_name_subtemplate(it) for it in inner_templates_param
        )

    @classmethod
    def _make_inners(cls, inner_templates):
        ret = {}
        for name, template in inner_templates.items():
            inner = template()

            if ret.setdefault(name, inner) is not inner:
                raise TypeError(f'duplicate inner name: {name}')
        return ret

    @classmethod
    def inner_templates_values(cls, inner_templates):
        return inner_templates.values()

    @classmethod
    def inners_items(cls, inners):
        return inners.items()

    @classmethod
    def init_result(cls):
        return {}

    @classmethod
    def insert_result(cls, res, key, value):
        res[key] = value

    @classmethod
    def result_zip_subwidget(cls, res, inners):
        for k, v in res.items():
            sw = inners.get(k)
            yield (k, v), sw

    def _from_json(self, d: dict, exact=True):
        if not isinstance(d, dict):
            raise PlaintextParseError(f'expected dict, got {type(d).__name__}')
        not_seen = dict(self.inners)

        ret = {}

        for k, v in d.items():
            subwidget = not_seen.pop(k, None)
            if not subwidget:
                if exact:
                    raise PlaintextParseError(f'key {k} has no appropriate widget')
                continue
            if not isinstance(v, str):
                # todo if you get a non-str value, just json-encode it and pass it on?
                raise PlaintextParseError(f'in key: {k}, value must be str, got {type(v).__name__}')

            try:
                parsed = subwidget.joined_plaintext_parser(v)
            except PlaintextParseError as e:
                raise PlaintextParseError(f'error parsing {k}') from e

            ret[k] = parsed

        if exact and not_seen:
            k, _ = not_seen.popitem()
            raise PlaintextParseError(f'key not found: {k}') from KeyError(k)

        return ret

    def _to_json(self, d: Mapping[str, object]):
        if not isinstance(d, Mapping):
            raise PlaintextPrintError from TypeError('can only accept dict')
        ret = {}
        for k, subwidget in self.inners.items():
            if k not in d:
                raise PlaintextPrintError('f{k} missing')
            v = d[k]
            try:
                s = subwidget.joined_plaintext_printer(v)
            except PlaintextPrintError as e:
                raise PlaintextPrintError(f'error printing {k}') from e
            ret[k] = s
        return ret

    @staticmethod
    def _to_name_subtemplate(option: NamedTemplate) -> Tuple[str, FidgetTemplate[T]]:
        try:
            template = option.template_of()
        except AttributeError:
            name, option = option
            option = option.template_of()
            return name, option

        if not template.title:
            raise ValueError(f'inner template {option} must have a title')
        return template.title, template

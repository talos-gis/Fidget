from typing import Optional, Pattern, Union, Container

import re

from fidget.core import Fidget, ValidationError, inner_plaintext_parser
from fidget.core.__util__ import first_valid, optional_valid


class FidgetRawString(Fidget[str]):
    PATTERN = None
    ALLOWED_CHARACTERS: Container[str] = None
    FORBIDDEN_CHARACTERS: Container[str] = None
    INITIAL = ''

    def __init__(self, title: str, pattern: Union[str, Pattern[str]] = None,
                 allowed_characters: Container[str] = None, forbidden_characters: Container[str] = None,
                 initial=None, **kwargs):
        super().__init__(title, **kwargs)

        pattern = optional_valid(pattern=pattern, PATTERN=self.PATTERN, _self=self)

        self.pattern: Optional[Pattern[str]] = re.compile(pattern) if isinstance(pattern, str) else pattern
        self.allowed_characters = optional_valid(allowed_characters=allowed_characters,
                                                 ALLOWED_CHARACTERS=self.ALLOWED_CHARACTERS, _self=self)
        self.forbidden_characters = optional_valid(forbidden_characters=forbidden_characters,
                                                   FORBIDDEN_CHARACTERS=self.FORBIDDEN_CHARACTERS, _self=self)
        self.initial = first_valid(initial=initial, INITIAL=self.INITIAL, _self=self)

    def fill_initial(self):
        self.fill_value(self.initial)

    def validate(self, value):
        super().validate(value)
        if self.pattern and not self.pattern.fullmatch(value):
            raise ValidationError(f'value must match pattern {self.pattern}', offender=self)
        if self.allowed_characters is not None:
            try:
                i, c = next(
                    ((i, c) for (i, c) in enumerate(value) if c not in self.allowed_characters)
                )
            except StopIteration:
                pass
            else:
                raise ValidationError(f'character {c} (position {i}) is not allowed', offender=self)
        if self.forbidden_characters is not None:
            try:
                i, c = next(
                    ((i, c) for (i, c) in enumerate(value) if c in self.forbidden_characters)
                )
            except StopIteration:
                pass
            else:
                raise ValidationError(f'character {c} (position {i}) is forbidden', offender=self)

    fill_stylesheet = None

    def indication_changed(self, value):
        super().indication_changed(value)
        if self.fill_stylesheet:
            if value.is_ok():
                self.fill_stylesheet('')
            else:
                self.fill_stylesheet('color: red;')

    @inner_plaintext_parser
    @staticmethod
    def raw_text(v):
        return v

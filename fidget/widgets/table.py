from typing import TypeVar, Generic, List, Iterable, Callable, NamedTuple, Type

from itertools import chain
from io import StringIO
import csv
from collections import namedtuple

from fidget.core.plaintext_adapter import high_priority

from fidget.backend.QtWidgets import QGridLayout, QHBoxLayout, QPushButton, QMenu, QApplication, QVBoxLayout, \
    QScrollArea, QWidget, QLabel
from fidget.backend.QtCore import Qt
from fidget.backend.QtGui import QCursor
from fidget.backend.Resources import add_row_below_icon, add_row_above_icon, del_row_icon

from fidget.core import TemplateLike, Fidget, FidgetTemplate, ParseError, ValidationError, \
    inner_plaintext_printer, inner_plaintext_parser, json_parser, PlaintextPrintError, PlaintextParseError, json_printer
from fidget.core.__util__ import first_valid, update

from fidget.widgets.idiomatic_inner import MultiFidgetWrapper
from fidget.widgets.user_util import FidgetInt
from fidget.widgets.confirmer import FidgetQuestion
from fidget.widgets.__util__ import only_valid, last_focus_proxy, repeat_last, valid_between, CountBounds, \
    table_printer, to_identifier

T = TypeVar('T')


# todo document


# todo fill for specific rows/columns


class FidgetTable(Generic[T], MultiFidgetWrapper[object, List[NamedTuple]]):
    def __init__(self, title: str, inner_templates: Iterable[TemplateLike[T]] = None, layout_cls=None,
                 rows: CountBounds = None,
                 row_button_text_func: Callable[[int], str] = None,
                 scrollable=None,
                 **kwargs):
        self.row_bounds = CountBounds[first_valid(rows=rows, ROWS=self.ROWS, _self=self)]

        inner_templates = tuple(
            t.template_of() for t in
            only_valid(inner_templates=inner_templates, INNER_TEMPLATES=self.INNER_TEMPLATES, _self=self)
        )

        super().__init__(title, **kwargs)

        self.inner_templates = inner_templates
        self.row_button_text_func = first_valid(row_button_text_func=row_button_text_func,
                                                ROW_BUTTON_TEXT_FUNC=self.ROW_BUTTON_TEXT_FUNC, _self=self)

        self.grid_layout: QGridLayout = None
        self.inners: List[List[Fidget[T]]] = None  # first row, then column, self.inners[row][column]
        self.col_labels: List[QLabel[T]] = None
        self.row_btns: List[QPushButton[T]] = None

        self.row_offset = 1
        self.col_offset = None

        self.row_count = 0
        self.column_count = None

        self.value_type: Type[NamedTuple] = None

        self.init_ui(layout_cls=layout_cls, scrollable=scrollable)

    INNER_TEMPLATES: Iterable[FidgetTemplate[T]] = None
    LAYOUT_CLS = QHBoxLayout
    ROWS = 1
    ROW_BUTTON_TEXT_FUNC: Callable[[int], str] = staticmethod(str)
    SCROLLABLE = True

    def init_ui(self, layout_cls=None, scrollable=None):
        super().init_ui()
        layout_cls = first_valid(layout_cls=layout_cls, LAYOUT_CLS=self.LAYOUT_CLS, _self=self)

        owner = self
        scrollable = first_valid(scrollable=scrollable, SCROLLABLE=self.SCROLLABLE, _self=self)

        owner_layout = QVBoxLayout()
        owner.setLayout(owner_layout)

        if scrollable:
            owner = QScrollArea(owner)
            owner.setWidgetResizable(True)
            owner_layout.addWidget(owner)

        master = QWidget()
        master_layout = layout_cls(master)

        if scrollable:
            owner.setWidget(master)
        else:
            owner_layout.addWidget(master)

        self.inners = []
        self.col_labels = []
        self.row_btns = []

        title_in_grid = not self.row_bounds.is_const

        self.col_offset = int(not self.row_bounds.is_const)

        if title_in_grid:
            exclude = (self.title_label,)
        else:
            exclude = ()

        with self.setup_provided(master_layout, exclude=exclude), self.suppress_update(call_on_exit=False):
            self.grid_layout = QGridLayout()

            field_names = []
            for i, column_template in enumerate(self.inner_templates):
                title = column_template.title or '_' + str(i)
                label = QLabel(title)
                field_names.append(title)
                self.col_labels.append(label)
                self.grid_layout.addWidget(label, 0, i + self.col_offset)

            self.column_count = len(self.inner_templates)

            for i in range(self.row_bounds.initial):
                self.add_row(i)

            master_layout.addLayout(self.grid_layout)

        self.value_type = namedtuple(to_identifier(self.title), (to_identifier(i.title) for i in self.inners),
                                     rename=True)

        if title_in_grid and self.title_label:
            self.grid_layout.addWidget(self.title_label, 0, 0)

        # self.setLayout(master_layout)
        self.apply_matrix()

        return master_layout

    def add_row(self, row):
        # make room
        for row_to_move in range(self.row_count - 1, row - 1, -1):
            for col, widget in enumerate(self.inners[row_to_move]):
                self.grid_layout.removeWidget(widget)
                self.grid_layout.addWidget(widget, row_to_move + self.row_offset + 1, col + self.col_offset)

        # add the new row
        new_row = []
        for col in range(self.column_count):
            inner = self._make_inner(col)
            new_row.append(inner)
            self.grid_layout.addWidget(inner, row + self.row_offset, col + self.col_offset)
        self.inners.insert(row, new_row)
        self.row_count += 1

        # add the new button (to the last row, buttons don't move around)
        if not self.row_bounds.is_const:
            new_button = self.row_btn(self.row_count - 1)
            self.grid_layout.addWidget(new_button, self.row_count + self.row_offset - 1, 0)
            self.row_btns.append(new_button)

    def row_btn(self, row_index):
        ret = QPushButton(self.row_button_text_func(row_index))
        ret.setFocusPolicy(Qt.ClickFocus)
        menu = QMenu(ret)

        def add_top():
            self.add_row(row_index)
            self.apply_matrix()

        def add_many_top():
            question = FidgetQuestion(
                FidgetInt('# of rows to add', validation_func=valid_between(1,
                                                                            None if self.row_bounds.max is None else (
                                                                                    self.row_bounds.max - self.row_count)
                                                                            )),
                cancel_value=None
            )
            response = question.exec_()
            if not response.is_ok():
                return
            value = response.value
            if not value:
                return
            for _ in range(value):
                self.add_row(row_index)
            self.apply_matrix()

        def add_bottom():
            self.add_row(row_index + 1)
            self.apply_matrix()

        def add_many_bottom():
            question = FidgetQuestion(
                FidgetInt('# of rows to add', validation_func=valid_between(1,
                                                                            None if self.row_bounds.max is None else (
                                                                                    self.row_bounds.max - self.row_count)
                                                                            )),
                cancel_value=None
            )
            response = question.exec_()
            if not response.is_ok():
                return
            value = response.value
            if not value:
                return
            for _ in range(value):
                self.add_row(row_index + 1)
            self.apply_matrix()

        # todo delete many?
        def del_():
            self.del_row(row_index)
            self.apply_matrix()

        ret.add_top_action = menu.addAction(add_row_above_icon(), 'add row above', add_top)
        ret.add_top_action.setEnabled(False)

        ret.add_many_top_action = menu.addAction('add rows above', add_many_top)
        ret.add_many_top_action.setEnabled(False)

        ret.add_bottom_action = menu.addAction(add_row_below_icon(), 'add row below',
                                               add_bottom)
        ret.add_bottom_action.setEnabled(False)

        ret.add_many_bottom_action = menu.addAction('add rows below', add_many_bottom)
        ret.add_many_bottom_action.setEnabled(False)

        ret.del_action = menu.addAction(del_row_icon(), 'delete row', del_)
        ret.del_action.setEnabled(False)

        @ret.clicked.connect
        def _(a):
            menu.exec_(QCursor.pos())

        return ret

    def del_row(self, row):
        # clear the the row
        for widget in self.inners[row]:
            widget.hide()
            self.grid_layout.removeWidget(widget)

        # shift all rows above one row down, clearing the last row
        for row_to_move in range(row + 1, self.row_count):
            for col, widget in enumerate(self.inners[row_to_move]):
                self.grid_layout.removeWidget(widget)
                self.grid_layout.addWidget(widget, row_to_move + self.row_offset - 1, col + self.col_offset)

        self.inners.pop(row)
        self.row_count -= 1

        # delete the button
        btn = self.row_btns.pop(-1)
        self.grid_layout.removeWidget(btn)
        btn.hide()

    def apply_matrix(self):
        """
        Apply whatever adjustments need to be made when the table changes dimensions
        """
        i = (last_focus_proxy(a) for a in chain.from_iterable(self.inners))
        try:
            prev = next(i)
        except StopIteration:
            pass
        else:
            for inner in i:
                self.setTabOrder(prev, inner)
                prev = inner

        can_add_row = self.row_bounds.in_bounds(self.row_count + 1)
        can_del_row = self.row_bounds.in_bounds(self.row_count - 1)
        for btn in self.row_btns:
            btn.add_top_action.setEnabled(can_add_row)
            btn.add_many_top_action.setEnabled(can_add_row)
            btn.add_bottom_action.setEnabled(can_add_row)
            btn.add_many_bottom_action.setEnabled(can_add_row)
            btn.del_action.setEnabled(can_del_row)

        self.change_value()

    def _make_inner(self, column_number):
        ret: Fidget[T] = self.inner_templates[column_number]()
        ret.on_change.connect(self.change_value)

        return ret

    def parse(self):
        ret = []
        for i, inner_row in enumerate(self.inners):
            row = []
            for field_name, inner in zip(self.value_type._fields, inner_row):
                try:
                    row.append(inner.maybe_parse())
                except ParseError as e:
                    raise ParseError(f'error parsing {i}[{field_name}]', offender=inner) from e
            ret.append(self.value_type._make(row))
        return ret

    def validate(self, value: List[List[T]]):
        for i, (inner_row, v_row) in enumerate(zip(self.inners, value)):
            for field_name, (inner, v) in zip(self.value_type._fields, zip(inner_row, v_row)):
                try:
                    inner.maybe_validate(v)
                except ValidationError as e:
                    raise ValidationError(f'error validating {i}[{field_name}]', offender=inner) from e

    def fill(self, v):
        rows = len(v)
        same_dims = True

        if rows < self.row_count:
            for _ in range(self.row_count - rows):
                self.del_row(self.row_count - 1)
        elif rows > self.row_count:
            for _ in range(rows - self.row_count):
                self.add_row(self.row_count)
        else:
            same_dims += 1

        for row, inners_row in zip(v, self.inners):
            for e, inner in zip(row, inners_row):
                inner.fill_value(e)

        if same_dims < 1:
            self.apply_matrix()

    # todo allow csv dialects
    @inner_plaintext_parser
    def from_csv(self, v):
        source = StringIO(v, newline='')
        v = list(csv.reader(source))

        ret = []
        row_count = len(v)
        if not row_count:
            raise PlaintextParseError('list must have at least one row')
        if not self.row_bounds.in_bounds(row_count):
            raise PlaintextParseError(f'row number {row_count} is out of bounds')
        col_count = len(v[0])
        if col_count != self.column_count:
            raise PlaintextParseError(f'column number mismatch {col_count} (expected {self.column_count})')

        for row_num, (row, inners_row) in enumerate(zip(v, repeat_last(self.inners))):
            ret_row = []
            if len(row) != col_count:
                raise PlaintextParseError(f'{col_count} column in row, 0 but {len(row)} in row {row_num}')
            for col_num, (e, inner) in enumerate(zip(row, repeat_last(inners_row))):
                try:
                    s = inner.joined_plaintext_parser(e)
                except PlaintextParseError as exc:
                    raise PlaintextParseError(f'error parsing {row_num, col_num}') from exc

                ret_row.append(s)
            ret.append(ret_row)

        return ret

    @inner_plaintext_printer
    def to_csv(self, v):
        ret = StringIO(newline='')
        writer = csv.writer(ret)
        for row in self.string_matrix(v):
            writer.writerow(row)
        return ret.getvalue()

    to_csv.__name__ = 'csv'

    @inner_plaintext_printer
    @high_priority
    @json_printer
    def to_json(self, v):
        return self.string_matrix(v)

    @inner_plaintext_parser
    @json_parser(list)
    def from_json(self, v):
        ret = []
        row_count = len(v)
        if not row_count:
            raise PlaintextParseError('list must have at least one row')
        if not self.row_bounds.in_bounds(row_count):
            raise PlaintextParseError(f'row number {row_count} is out of bounds')
        col_count = len(v[0])
        if col_count != self.column_count:
            raise PlaintextParseError(f'column number mismatch {col_count} (expected {self.column_count})')

        for row_num, (row, inners_row) in enumerate(zip(v, repeat_last(self.inners))):
            ret_row = []
            if not isinstance(row, list):
                raise PlaintextParseError(f'element in index {row_num} is not a list')
            if len(row) != col_count:
                raise PlaintextParseError(f'{col_count} column in row 0, but {len(row)} in row {row_num}')
            for col_num, (e, inner) in enumerate(zip(row, repeat_last(inners_row))):
                try:
                    s = inner.joined_plaintext_parser(e)
                except PlaintextParseError as exc:
                    raise PlaintextParseError(f'error parsing {row_num, col_num}') from exc

                ret_row.append(s)
            ret.append(ret_row)

        return ret

    @json_parser(list)
    def from_json_reshape(self, v):
        def rec_iter(iterable):
            for i in iterable:
                if isinstance(i, Iterable) and not isinstance(i, str):
                    yield from rec_iter(i)
                else:
                    yield i

        size = self.row_count * self.column_count
        i = rec_iter(v)
        ret = []
        for row_num, inners_row in enumerate(self.inners):
            ret_row = []
            for col_num, inner in enumerate(inners_row):
                try:
                    e = next(i)
                except StopIteration as exc:
                    raise PlaintextParseError(f'too few elements, expected {size}') from exc

                try:
                    s = inner.joined_plaintext_parser(e)
                except PlaintextParseError as exc:
                    raise PlaintextParseError(f'error parsing {row_num, col_num}') from exc

                ret_row.append(s)
            ret.append(ret_row)

        try:
            next(i)
        except StopIteration:
            pass
        else:
            raise PlaintextParseError(f'too many elements, expected {size}')
        return ret

    markdown = inner_plaintext_printer(update(__name__='markdown')(table_printer((
        ('|', '|'),
        ('|', '|'),
        ('|', '|')
    ), '|', '\n', header_row=lambda self: self.value_type._fields)))

    def plaintext_parsers(self):
        yield from super().plaintext_parsers()
        yield maks(self.from_json_reshape, __explicit__=not self.is_constant_size)

    def string_matrix(self, v):
        ret = []
        for row_num, (row, inners_row) in enumerate(zip(v, self.inners)):
            ret_row = []
            for col_num, (e, inner) in enumerate(zip(row, inners_row)):
                try:
                    s = inner.joined_plaintext_printer(e)
                except PlaintextPrintError as exc:
                    raise PlaintextPrintError(f'error printing {row_num, col_num}') from exc

                ret_row.append(s)
            ret.append(ret_row)

        return ret

    @property
    def is_constant_size(self):
        return self.row_bounds.is_const

    def keyPressEvent(self, event):
        def mutate_focus(ro, co):
            focus = QApplication.focusWidget()
            index = -1
            while index == -1:
                focus = focus.parent()
                if not focus:
                    event.ignore()
                    return
                index = self.grid_layout.indexOf(focus)
            r, c, *_ = self.grid_layout.getItemPosition(index)
            r += ro
            c += co
            if r <= 0 or c <= 0:
                # avoid row/column buttons
                event.ignore()
                return
            item = self.grid_layout.itemAtPosition(r, c)
            if not item:
                event.ignore()
                return
            to_focus = item.widget()
            to_focus.setFocus()

        if event.key() == Qt.Key_Down:
            mutate_focus(1, 0)
        if event.key() == Qt.Key_Up:
            mutate_focus(-1, 0)
        if event.key() == Qt.Key_Right:
            mutate_focus(0, 1)
        if event.key() == Qt.Key_Left:
            mutate_focus(0, -1)
        else:
            super().keyPressEvent(event)

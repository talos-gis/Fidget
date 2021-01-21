from typing import TypeVar, Generic, List, Iterable, Callable

from itertools import chain
from io import StringIO
import csv

from fidget.core.plaintext_adapter import high_priority

from fidget.backend.QtWidgets import QGridLayout, QHBoxLayout, QPushButton, QMenu, QStyle, QApplication, QVBoxLayout, \
    QScrollArea, QWidget, QSizePolicy
from fidget.backend.QtCore import Qt
from fidget.backend.QtGui import QCursor
from fidget.backend.Resources import add_row_above_icon, add_row_below_icon, add_col_left_icon, add_col_right_icon,\
    del_row_icon, del_col_icon

from fidget.core import TemplateLike, Fidget, FidgetTemplate, ParseError, ValidationError, \
    inner_plaintext_printer, inner_plaintext_parser, json_parser, PlaintextPrintError, PlaintextParseError, json_printer
from fidget.core.__util__ import first_valid, mask, update

from fidget.widgets.idiomatic_inner import SingleFidgetWrapper
from fidget.widgets.user_util import FidgetInt
from fidget.widgets.confirmer import FidgetQuestion
from fidget.widgets.__util__ import only_valid, last_focus_proxy, repeat_last, valid_between, CountBounds, \
    table_printer

T = TypeVar('T')


# todo document


# todo fill for specific rows/columns


class FidgetMatrix(Generic[T], SingleFidgetWrapper[T, List[List[T]]]):
    def __init__(self, inner_template: TemplateLike[T] = None, layout_cls=None,
                 rows: CountBounds = None, columns: CountBounds = None,
                 row_button_text_func: Callable[[int], str] = None,
                 column_button_text_func: Callable[[int], str] = None,
                 scrollable=None,
                 **kwargs):
        self.row_bounds = CountBounds[first_valid(rows=rows, ROWS=self.ROWS, _self=self)]
        self.column_bounds = CountBounds[first_valid(columns=columns, COLUMNS=self.COLUMNS, _self=self)]

        inner_template = only_valid(inner_template=inner_template, INNER_TEMPLATE=self.INNER_TEMPLATE, _self=self).template_of()

        super().__init__(inner_template.title, **kwargs)

        self.inner_template = inner_template
        self.row_button_text_func = first_valid(row_button_text_func=row_button_text_func,
                                                ROW_BUTTON_TEXT_FUNC=self.ROW_BUTTON_TEXT_FUNC, _self=self)
        self.column_button_text_func = first_valid(column_button_text_func=column_button_text_func,
                                                   COLUMN_BUTTON_TEXT_FUNC=self.COLUMN_BUTTON_TEXT_FUNC, _self=self)
        if self.column_button_text_func is ...:
            self.column_button_text_func = self.row_button_text_func

        self.grid_layout: QGridLayout = None
        self.inners: List[List[Fidget[T]]] = None  # first row, then column, self.inners[row][column]
        self.col_btns: List[QPushButton[T]] = None
        self.row_btns: List[QPushButton[T]] = None

        self.row_offset = None
        self.col_offset = None

        self.row_count = 0
        self.column_count = 0

        self.init_ui(layout_cls=layout_cls, scrollable=scrollable)

    INNER_TEMPLATE: FidgetTemplate[T] = None
    LAYOUT_CLS = QHBoxLayout
    ROWS = 1
    COLUMNS = 1
    ROW_BUTTON_TEXT_FUNC: Callable[[int], str] = staticmethod(str)
    COLUMN_BUTTON_TEXT_FUNC: Callable[[int], str] = ...
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
        self.col_btns = []
        self.row_btns = []

        title_in_grid = not (self.row_bounds.is_const or self.column_bounds.is_const)

        self.row_offset = int(not self.column_bounds.is_const)
        self.col_offset = int(not self.row_bounds.is_const)

        if title_in_grid:
            exclude = (self.title_label,)
        else:
            exclude = ()

        with self.setup_provided(master_layout, exclude=exclude), self.suppress_update(call_on_exit=False):
            self.grid_layout = QGridLayout()

            for i in range(self.row_bounds.initial):
                self.add_row(i)

            for i in range(self.column_bounds.initial):
                self.add_col(i)

            master_layout.addLayout(self.grid_layout)

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
            inner = self._make_inner()
            new_row.append(inner)
            self.grid_layout.addWidget(inner, row + self.row_offset, col + self.col_offset)
        self.inners.insert(row, new_row)
        self.row_count += 1

        # add the new button (to the last row, buttons don't move around)
        if not self.row_bounds.is_const:
            new_button = self.row_btn(self.row_count - 1)
            self.grid_layout.addWidget(new_button, self.row_count + self.row_offset - 1, 0)
            self.row_btns.append(new_button)

    def add_col(self, col):
        # make room
        for col_to_move in range(self.column_count - 1, col - 1, -1):
            for row in range(self.row_count):
                widget = self.inners[row][col_to_move]
                self.grid_layout.removeWidget(widget)
                self.grid_layout.addWidget(widget, row + self.row_offset, col_to_move + self.col_offset + 1)

        for row_num in range(self.row_count):
            inner = self._make_inner()
            self.inners[row_num].insert(col, inner)
            self.grid_layout.addWidget(inner, row_num + self.row_offset, col + self.col_offset)

        self.column_count += 1

        # add the new button (to the last column, buttons don't move around)
        if not self.column_bounds.is_const:
            new_button = self.col_btn(self.column_count - 1)
            self.grid_layout.addWidget(new_button, 0, self.column_count + self.col_offset - 1)
            self.col_btns.append(new_button)

    def row_btn(self, row_index):
        ret = QPushButton(self.row_button_text_func(row_index))
        ret.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
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

        # todo check if inner has fill
        def clone():
            self.add_row(row_index+1)
            for c in range(self.column_count):
                v = self.inners[row_index][c].value()
                if v.is_ok() and self.inners[row_index+1][c].fill is not None:
                    self.inners[row_index+1][c].fill_value(v.value)
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

        ret.clone_action = menu.addAction('clone', clone)
        ret.clone_action.setEnabled(False)

        @ret.clicked.connect
        def _(a):
            menu.exec_(QCursor.pos())

        return ret

    def col_btn(self, col_index):
        ret = QPushButton(self.column_button_text_func(col_index))
        ret.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        ret.setFocusPolicy(Qt.ClickFocus)
        menu = QMenu(ret)

        def add_left():
            self.add_col(col_index)
            self.apply_matrix()

        def add_many_left():
            question = FidgetQuestion(
                FidgetInt('# of columns to add',
                          validation_func=valid_between(1, None if self.column_bounds.max is None else (
                                  self.column_bounds.max - self.column_count))),
                cancel_value=None
            )
            response = question.exec_()
            if not response.is_ok():
                return
            value = response.value
            if not value:
                return
            for _ in range(value):
                self.add_col(col_index)
            self.apply_matrix()

        def add_right():
            self.add_col(col_index + 1)
            self.apply_matrix()

        def add_many_right():
            question = FidgetQuestion(
                FidgetInt('# of columns to add',
                          validation_func=valid_between(1, None if self.column_bounds.max is None else (
                                  self.column_bounds.max - self.column_count))),
                cancel_value=None
            )
            response = question.exec_()
            if not response.is_ok():
                return
            value = response.value
            if not value:
                return
            for _ in range(value):
                self.add_col(col_index + 1)
            self.apply_matrix()

        # todo delete many?
        def del_():
            self.del_col(col_index)
            self.apply_matrix()

        # todo check if inner has fill
        def clone():
            self.add_row(col_index + 1)
            for r in range(self.row_count):
                v = self.inners[r][col_index].value()
                if v.is_ok() and self.inners[r][col_index+1].fill is not None:
                    self.inners[r][col_index+1].fill_value(v.value)
            self.apply_matrix()

        ret.add_left_action = menu.addAction(add_col_left_icon(), 'add column left',
                                             add_left)
        ret.add_left_action.setEnabled(False)

        ret.add_many_left_action = menu.addAction('add columns left', add_many_left)
        ret.add_many_left_action.setEnabled(False)

        ret.add_right_action = menu.addAction(add_col_right_icon(), 'add column right',
                                              add_right)
        ret.add_right_action.setEnabled(False)

        ret.add_many_right_action = menu.addAction('add columns right', add_many_right)
        ret.add_many_right_action.setEnabled(False)

        ret.del_action = menu.addAction(del_col_icon(), 'delete column', del_)
        ret.del_action.setEnabled(False)

        ret.clone_action = menu.addAction('clone', clone)
        ret.clone_action.setEnabled(False)

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

    def del_col(self, col):
        # clear the the column
        for row in self.inners:
            widget = row[col]
            widget.hide()
            self.grid_layout.removeWidget(widget)

        # shift all columns above one column down, clearing the last column
        for col_to_move in range(col + 1, self.column_count):
            for row_num, row in enumerate(self.inners):
                widget = row[col_to_move]
                self.grid_layout.removeWidget(widget)
                self.grid_layout.addWidget(widget, row_num + self.row_offset, col_to_move + self.col_offset - 1)

        for row in self.inners:
            row.pop(col)
        self.column_count -= 1

        # delete the button
        btn = self.col_btns.pop(-1)
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
            btn.clone_action.setEnabled(can_add_row)

        can_add_col = self.column_bounds.in_bounds(self.column_count + 1)
        can_del_col = self.column_bounds.in_bounds(self.column_count - 1)
        for btn in self.col_btns:
            btn.add_left_action.setEnabled(can_add_col)
            btn.add_many_left_action.setEnabled(can_add_col)
            btn.add_right_action.setEnabled(can_add_col)
            btn.add_many_right_action.setEnabled(can_add_col)
            btn.del_action.setEnabled(can_del_col)
            btn.clone_action.setEnabled(can_add_col)

        self.change_value()

    def _make_inner(self):
        ret: Fidget[T] = self.inner_template()
        ret.on_change.connect(self.change_value)

        return ret

    def parse(self):
        ret = []
        for i, inner_row in enumerate(self.inners):
            row = []
            for j, inner in enumerate(inner_row):
                try:
                    row.append(inner.maybe_parse())
                except ParseError as e:
                    raise ParseError(f'error parsing {i, j}', offender=inner) from e
            ret.append(row)
        return ret

    def validate(self, value: List[List[T]]):
        for i, (inner_row, v_row) in enumerate(zip(self.inners, value)):
            for j, (inner, v) in enumerate(zip(inner_row, v_row)):
                try:
                    inner.maybe_validate(v)
                except ValidationError as e:
                    raise ValidationError(f'error validating {i, j}', offender=inner) from e

    def indication_changed(self, value):
        Fidget.indication_changed(self, value)

    def fill(self, v):
        rows = len(v)
        cols = len(v[0])
        same_dims = 0

        if rows < self.row_count:
            for _ in range(self.row_count - rows):
                self.del_row(self.row_count - 1)
        elif rows > self.row_count:
            for _ in range(rows - self.row_count):
                self.add_row(self.row_count)
        else:
            same_dims += 1

        if cols < self.column_count:
            for _ in range(self.column_count - cols):
                self.del_col(self.column_count - 1)
        elif cols > self.column_count:
            for _ in range(cols - self.column_count):
                self.add_col(self.column_count)
        else:
            same_dims += 1

        for row, inners_row in zip(v, self.inners):
            for e, inner in zip(row, inners_row):
                inner.fill_value(e)

        if same_dims < 2:
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
        if not self.column_bounds.in_bounds(col_count):
            raise PlaintextParseError(f'column number {col_count} is out of bounds')

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
        if not self.column_bounds.in_bounds(col_count):
            raise PlaintextParseError(f'column number {col_count} is out of bounds')

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

    matrix = inner_plaintext_printer(update(__name__='matrix')(table_printer((
        ('/', '\\'),
        ('|', '|'),
        ('\\', '/')
    ), ',', '\n')))

    markdown = inner_plaintext_printer(update(__name__='markdown')(table_printer((
        ('|', '|'),
        ('|', '|'),
        ('|', '|')
    ), '|', '\n')))

    def plaintext_parsers(self):
        yield from super().plaintext_parsers()
        yield mask(self.from_json_reshape, __explicit__=not self.is_constant_size)

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
        return self.row_bounds.is_const and self.column_bounds.is_const

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

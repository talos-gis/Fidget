from typing import TypeVar, Generic, List, Optional

from fidget.backend.QtWidgets import QGridLayout, QHBoxLayout, QPushButton

from fidget.core import TemplateLike, Fidget, FidgetTemplate
from fidget.core.__util__ import first_valid

from fidget.widgets.idiomatic_inner import SingleFidgetWrapper
from fidget.widgets.__util__ import only_valid

T = TypeVar('T')


# todo document

class CountBounds:
    def __init__(self, initial: int, min: Optional[int] = None, max: Optional[int] = None):
        self.initial = initial
        self.max = max
        self.min = min

    def in_bounds(self, num):
        if self.min is not None and num < self.min:
            return False
        if self.max is not None and num >= self.max:
            return False
        return True

    def __class_getitem__(cls, item):
        if isinstance(item, int):
            return cls(item, item, item + 1)
        if isinstance(item, slice):
            initial = item.start or 1
            min = item.stop
            max = item.step
            return cls(initial, min, max)
        if isinstance(item, cls):
            return item
        return cls(*item)


class FidgetMatrix(Generic[T], SingleFidgetWrapper[List[List[T]]]):
    def __init__(self, inner_template: TemplateLike[T] = None, layout_cls=None,
                 rows: CountBounds = None, columns: CountBounds = None,
                 **kwargs):
        self.row_bounds = CountBounds[first_valid(rows=rows, ROWS=self.ROWS)]
        self.column_bounds = CountBounds[first_valid(columns=columns, COLUMNS=self.COLUMNS)]

        inner_template = only_valid(inner_template=inner_template, INNER_TEMPLATE=self.INNER_TEMPLATE).template_of()

        super().__init__(inner_template.title, **kwargs)

        self.inner_template = inner_template

        self.grid_layout: QGridLayout = None
        self.inners: List[List[Fidget[T]]] = None  # first row, then column, self.inners[row][column]
        self.option_btn_cols: List[QPushButton[T]] = None
        self.option_btn_rows: List[QPushButton[T]] = None

        self.row_count = 0
        self.column_count = 0

        self.init_ui(layout_cls=layout_cls)

    def init_ui(self, layout_cls=None):
        super().init_ui()
        layout_cls = first_valid(layout_cls=layout_cls, LAYOUT_CLS=self.LAYOUT_CLS)
        master_layout = layout_cls()

        with self.setup_provided(master_layout, exclude=(self.title_label,)) \
                , self.suppress_update(call_on_exit=False):
            self.grid_layout = QGridLayout()
            for i in range(self.row_bounds.initial):
                self.add_row(i)

            for i in range(self.column_bounds.initial):
                self.add_col(i)
            master_layout.addLayout(self.grid_layout)

        if self.title_label:
            self.grid_layout.addWidget(self.title_label, 0, 0)

        self.setLayout(master_layout)

    def add_row(self, row):
        # make room
        for row_to_move in range(self.row_count, row - 1, -1):
            for col, widget in enumerate(self.inners[row_to_move]):
                self.grid_layout.addWidget(widget, row_to_move + 2, col + 1)

        # add the new row
        new_row = []
        for col in range(self.column_count):
            inner = self.inner_template()
            new_row.append(inner)
            self.grid_layout.addWidget(inner, row + 1, col + 1)
        self.inners.insert(row, new_row)

    def add_col(self, col):
        # make room
        for col_to_move in range(self.column_count, col - 1, -1):
            for row in range(self.row_count):
                widget = self.inners[row][col_to_move]
                self.grid_layout.addWidget(widget, row + 1, col_to_move + 2)

        for row_num in range(self.row_count):
            inner = self.inner_template()
            self.inners[row_num].insert(col, inner)
            self.grid_layout.addWidget(inner, row_num + 1, col + 1)

    INNER_TEMPLATE: FidgetTemplate[T] = None
    LAYOUT_CLS = QHBoxLayout
    ROWS = 1
    COLUMNS = 1

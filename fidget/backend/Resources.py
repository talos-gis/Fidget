from fidget.backend.QtGui import QIcon
# noinspection PyUnresolvedReferences
import fidget.backend._resources


class LazyIcon:
    def __init__(self, path):
        self.path = path
        self._instance = None

    def __call__(self, *args, **kwargs):
        if not self._instance:
            self._instance = QIcon(self.path)
        return self._instance


add_col_left_icon = LazyIcon(':fidget/feather/corner-left-down.svg')
add_col_right_icon = LazyIcon(':fidget/feather/corner-right-down.svg')

add_row_above_icon = LazyIcon(':fidget/feather/corner-up-right.svg')
add_row_below_icon = LazyIcon(':fidget/feather/corner-down-right.svg')

del_col_icon = LazyIcon(':fidget/feather/delete.svg')
del_row_icon = del_col_icon

error_icon = LazyIcon(':fidget/feather/alert-triangle.svg')
ok_icon = LazyIcon(':fidget/feather/check.svg')

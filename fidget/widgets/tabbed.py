from __future__ import annotations

from typing import Iterable

from fidget.backend.QtWidgets import QVBoxLayout, QTabWidget, QWidget
from fidget.backend.QtCore import Qt
from fidget.backend.Resources import ok_icon, error_icon

from fidget.widgets.mapping import FidgetMapping, NamedTemplate


# todo document

class FidgetTabs(FidgetMapping):
    def __init__(self, title, inner_templates: Iterable[NamedTemplate] = None, **kwargs):
        super().__init__(title, inner_templates, **kwargs)
        self.tabbed: QTabWidget = None
        self.summary_layout = None

        self.init_ui()

    INNER_TEMPLATES: Iterable[NamedTemplate] = None

    def init_ui(self):
        super().init_ui()

        layout = QVBoxLayout()

        self.tabbed = QTabWidget()
        self.summary_layout = QVBoxLayout()

        for name, inner in self.make_inners().items():
            inner.on_change.connect(self.change_value)
            self.tabbed.addTab(inner, name)

        with self.setup_provided(self.summary_layout):
            pass
        if self.summary_layout.count():
            summary = QWidget()
            summary.setLayout(self.summary_layout)
            self.tabbed.addTab(summary, 'summary')
        else:
            self.summary_layout = None

        layout.addWidget(self.tabbed)
        self.setLayout(layout)

        return layout

    def indication_changed(self, value):
        if self.summary_layout:
            icon = ok_icon if value.is_ok() else error_icon
            self.tabbed.setTabIcon(len(self.inners), icon())

    def keyPressEvent(self, event):
        def mutate_focus(change):
            curr_index = self.tabbed.currentIndex()
            curr_index += change
            self.tabbed.setCurrentIndex(curr_index)

        if event.key() == Qt.Key_Right:
            mutate_focus(1)
        if event.key() == Qt.Key_Left:
            mutate_focus(-1)
        else:
            super().keyPressEvent(event)

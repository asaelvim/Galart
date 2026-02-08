from PySide6.QtCore import QEvent
from PySide6.QtWidgets import QHBoxLayout, QFrame, QWidget
from PaletaColores import *
from BotonMenu import BotonMenu

class ItemMenu(QWidget):
    def __init__(self, text: str, selected: bool = False):
        super().__init__()

        self.selected = selected

        self.indicator = QFrame()
        self.indicator.setFixedSize(6, ALTURA_BOTON)
        self.indicator.setStyleSheet(f"background: {ACENTO}; border-radius: 3px;")
        self.indicator.setVisible(selected)

        self.button = BotonMenu(text, active=selected)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(10)
        lay.addWidget(self.indicator)
        lay.addWidget(self.button)

        self.installEventFilter(self)
        self.button.installEventFilter(self)
        self.indicator.installEventFilter(self)

    def set_selected(self, value: bool):
        self.selected = value
        self.indicator.setVisible(value)
        self._set_button_active(value)

    def _set_button_active(self, active: bool):
        self.button.setObjectName("MenuButtonActive" if active else "MenuButton")
        self.button.setStyleSheet(self.button._style())  # reaplica el CSS

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Enter:
            self.indicator.setVisible(True)
            self._set_button_active(True)
            return False

        if event.type() == QEvent.Leave:
            if not self.selected:
                self.indicator.setVisible(False)
                self._set_button_active(False)
            return False

        return super().eventFilter(obj, event)

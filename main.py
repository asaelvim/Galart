import sys
import random
from PySide6.QtCore import Qt, QSize, QEvent
from PySide6.QtGui import (
    QColor, QFont, QPainter, QLinearGradient, QPixmap
)
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QFrame, QPushButton, QGraphicsDropShadowEffect
)


BG_A = "#F7F4EF"
BG_B = "#F2ECE4"
SURFACE = "#FFFFFF"
BORDER = "#E7E1D8"
TEXT = "#1F1F1F"
MUTED = "#5B5B5B"

PRIMARY = "#111827"
GOLD = "#C8A24A"

BTN_H = 40
BTN_SPACING = 10
BTN_BG = "#F6F1EA"
BTN_BORDER = "#DED6CC"
BTN_TEXT = "#2A2A2A"
ACTIVE_BG = "#2F333A"
ACTIVE_TEXT = "#FFFFFF"

class Background(QWidget):
    def __init__(self):
        super().__init__()
        self._noise = self._make_noise_tile(160, 160, alpha=14, seed=7)

    @staticmethod
    def _make_noise_tile(w: int, h: int, alpha: int = 12, seed: int = 1) -> QPixmap:
        rnd = random.Random(seed)
        pm = QPixmap(w, h)
        pm.fill(Qt.transparent)

        p = QPainter(pm)
        p.setRenderHint(QPainter.Antialiasing, False)

        for y in range(h):
            for x in range(w):
                v = rnd.randint(220, 245)
                p.setPen(QColor(v, v, v, alpha))
                p.drawPoint(x, y)

        p.end()
        return pm

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)

        grad = QLinearGradient(0, 0, 0, self.height())
        grad.setColorAt(0.0, QColor(BG_A))
        grad.setColorAt(1.0, QColor(BG_B))
        p.fillRect(self.rect(), grad)

        p.setOpacity(0.65)
        p.drawTiledPixmap(self.rect(), self._noise)
        p.setOpacity(1.0)

        p.end()


class Card(QFrame):
    def __init__(self):
        super().__init__()
        self.setObjectName("Card")
        self.setStyleSheet(f"""
            QFrame#Card {{
                background: {SURFACE};
                border: 1px solid {BORDER};
                border-radius: 22px;
            }}
        """)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(28)
        shadow.setOffset(0, 10)
        shadow.setColor(QColor(0, 0, 0, 55))
        self.setGraphicsEffect(shadow)


class MenuButton(QPushButton):
    def __init__(self, text: str, active: bool = False):
        super().__init__(text)

        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(BTN_H)

        self.setFont(QFont("Segoe UI", 12))
        self.setFocusPolicy(Qt.NoFocus)
        self.setAutoDefault(False)
        self.setDefault(False)

        self.setObjectName("MenuButtonActive" if active else "MenuButton")

        self.setStyleSheet(self._style())

    def _style(self) -> str:
        return f"""
            QPushButton#MenuButton {{
                background: {BTN_BG};
                color: {BTN_TEXT};
                border: 1px solid {BTN_BORDER};
                border-radius: 10px;
                text-align: left;
                padding-left: 26px;
            }}

            QPushButton#MenuButtonActive {{
                background: {ACTIVE_BG};
                color: {ACTIVE_TEXT};
                border: 1px solid {BTN_BORDER};
                border-radius: 10px;
                text-align: left;
                padding-left: 26px;
            }}
        """


class MenuItem(QWidget):
    def __init__(self, text: str, selected: bool = False):
        super().__init__()

        self.selected = selected

        self.indicator = QFrame()
        self.indicator.setFixedSize(6, BTN_H)
        self.indicator.setStyleSheet(f"background: {GOLD}; border-radius: 3px;")
        self.indicator.setVisible(selected)

        self.button = MenuButton(text, active=selected)

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


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Galería de Arte")
        self.setFixedSize(QSize(590, 829))

        root = Background()
        self.setCentralWidget(root)

        main = QVBoxLayout(root)
        main.setContentsMargins(0, 0, 0, 0)
        main.addStretch(3)

        card = Card()
        card.setFixedSize(590, 829)

        card_wrap = QHBoxLayout()
        card_wrap.addStretch(1)
        card_wrap.addWidget(card)
        card_wrap.addStretch(1)
        main.addLayout(card_wrap)

        main.addStretch(1)


        content = QVBoxLayout(card)
        content.setContentsMargins(42, 36, 42, 30)
        content.setSpacing(14)

        lbl_title = QLabel("Galería de Arte")
        lbl_title.setAlignment(Qt.AlignHCenter)
        lbl_title.setFont(QFont("Segoe UI", 28, QFont.Weight.DemiBold))
        lbl_title.setStyleSheet(f"color: {TEXT};")
        content.addWidget(lbl_title)

        lbl_sub = QLabel("Sistema de Ventas de Pinturas de Arte")
        lbl_sub.setAlignment(Qt.AlignHCenter)
        lbl_sub.setFont(QFont("Segoe UI", 12))
        lbl_sub.setStyleSheet(f"color: {MUTED};")
        content.addWidget(lbl_sub)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFixedHeight(1)
        line.setStyleSheet(f"background: {BORDER}; border: none;")
        content.addWidget(line)

        content.addSpacing(6)

        items = [
            "Gestión de Clientes",
            "Gestión de Proveedores",
            "Gestión de Vendedores",
            "Gestión de Pinturas",
            "Gestión de Artistas",
            "Cotizaciones",
            "Gestión de Ventas",
            "Gestión de Compras",
            "Reportes",
        ]
        
        self.menu_items = []

        for i, t in enumerate(items):
            it = MenuItem(t)
            self.menu_items.append(it)
            content.addWidget(it)
            content.addSpacing(BTN_SPACING)

        content.addStretch(1)


        btn_exit = QPushButton("Salir")
        btn_exit.setCursor(Qt.PointingHandCursor)
        btn_exit.setFixedHeight(40)
        btn_exit.setFont(QFont("Segoe UI", 13))
        btn_exit.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {MUTED};
                border: none;
            }}
            QPushButton:hover {{
                color: {PRIMARY};
                text-decoration: underline;
            }}
        """)

        btn_exit.clicked.connect(QApplication.instance().quit)

        content.addWidget(btn_exit, alignment=Qt.AlignHCenter)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    w = MainWindow()
    w.show()
    sys.exit(app.exec())

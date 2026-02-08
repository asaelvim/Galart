import random
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QLinearGradient, QPixmap
from PySide6.QtWidgets import QWidget
from modulos.PaletaColores import *

class Fondo(QWidget):
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
        grad.setColorAt(0.0, QColor(FONDO_A))
        grad.setColorAt(1.0, QColor(FONDO_B))
        p.fillRect(self.rect(), grad)

        p.setOpacity(0.65)
        p.drawTiledPixmap(self.rect(), self._noise)
        p.setOpacity(1.0)

        p.end()

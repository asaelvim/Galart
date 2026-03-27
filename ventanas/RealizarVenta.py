from __future__ import annotations

import re
from typing import Any, Dict, Optional

from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QFont, QIntValidator
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)


class RealizarVentaDialog(QDialog):
    def __init__(self, total: float, parent=None):
        super().__init__(parent)
        self.total = float(total)
        self.payment_data: Optional[Dict[str, Any]] = None

        self.setWindowTitle("Realizar Venta")
        self.setModal(True)
        self.setMinimumWidth(540)
        self.setObjectName("RealizarVentaDialog")

        self.cmbFormaPago = QComboBox()
        self.cmbFormaPago.addItem("Efectivo", "efectivo")
        self.cmbFormaPago.addItem("Tarjeta", "tarjeta")
        self.cmbFormaPago.currentIndexChanged.connect(self._update_page)

        self.stack = QStackedWidget()
        self._build_cash_page()
        self._build_card_page()

        self.lblTotal = QLabel(f"Total a cobrar: ${self.total:.2f}")
        self.lblTotal.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))

        self.btnConcretar = QPushButton("Concretar venta")
        self.btnConcretar.setCursor(Qt.PointingHandCursor)
        self.btnConcretar.clicked.connect(self.concretar_venta)

        self.btnCancelar = QPushButton("Cancelar")
        self.btnCancelar.setCursor(Qt.PointingHandCursor)
        self.btnCancelar.clicked.connect(self.reject)

        top = QVBoxLayout(self)
        top.setContentsMargins(18, 18, 18, 18)
        top.setSpacing(12)

        title = QLabel("Forma de pago")
        title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignHCenter)
        top.addWidget(title)

        top.addWidget(self.lblTotal)

        row_forma = QHBoxLayout()
        row_forma.addWidget(QLabel("Selecciona:"))
        row_forma.addWidget(self.cmbFormaPago)
        row_forma.addStretch(1)
        top.addLayout(row_forma)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setFixedHeight(1)
        top.addWidget(sep)

        top.addWidget(self.stack)

        row_btns = QHBoxLayout()
        row_btns.addStretch(1)
        row_btns.addWidget(self.btnCancelar)
        row_btns.addWidget(self.btnConcretar)
        top.addLayout(row_btns)

        self._update_page()
        self._actualizar_resumen_efectivo()

        self.setStyleSheet(
            """
            QDialog#RealizarVentaDialog {
                background: #F7F4EF;
                color: #2A2A2A;
                font-family: "Segoe UI";
                font-size: 10pt;
            }
            QLabel {
                color: #2A2A2A;
            }
            QComboBox, QLineEdit, QDoubleSpinBox {
                background: #FFFFFF;
                border: 1px solid #E7E1D8;
                border-radius: 8px;
                padding: 6px 10px;
                color: #2A2A2A;
            }
            QComboBox:focus, QLineEdit:focus, QDoubleSpinBox:focus {
                border: 1px solid #C8A24A;
            }
            QPushButton {
                background: #F6F1EA;
                color: #2A2A2A;
                border: 1px solid #DED6CC;
                border-radius: 9px;
                padding: 7px 14px;
            }
            QPushButton:hover {
                border: 1px solid #C8A24A;
                background: #F7F4EF;
            }
            QPushButton:pressed {
                background: #EFE7DD;
            }
            """
        )

    def _build_cash_page(self) -> None:
        page = QWidget()
        layout = QFormLayout(page)
        layout.setLabelAlignment(Qt.AlignLeft)
        layout.setFormAlignment(Qt.AlignTop)

        self.spnEfectivo = QDoubleSpinBox()
        self.spnEfectivo.setDecimals(2)
        self.spnEfectivo.setMinimum(0.00)
        self.spnEfectivo.setMaximum(999999999.99)
        self.spnEfectivo.setSingleStep(10.00)
        self.spnEfectivo.setPrefix("$")
        self.spnEfectivo.setValue(self.total)
        self.spnEfectivo.valueChanged.connect(self._actualizar_resumen_efectivo)

        layout.addRow("Cantidad recibida:", self.spnEfectivo)

        self.lblCambio = QLabel("Cambio: $0.00")
        self.lblCambio.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        layout.addRow(" ", self.lblCambio)

        self.lblFaltante = QLabel("Faltante: $0.00")
        self.lblFaltante.setFont(QFont("Segoe UI", 9))
        layout.addRow(" ", self.lblFaltante)

        self.stack.addWidget(page)

    def _build_card_page(self) -> None:
        page = QWidget()
        layout = QFormLayout(page)
        layout.setLabelAlignment(Qt.AlignLeft)
        layout.setFormAlignment(Qt.AlignTop)

        self.txtTarjeta = QLineEdit()
        self.txtTarjeta.setInputMask("0000 0000 0000 0000;_")
        self.txtTarjeta.setPlaceholderText("0000 0000 0000 0000")

        self.txtVencimiento = QLineEdit()
        self.txtVencimiento.setInputMask("00/00;_")
        self.txtVencimiento.setPlaceholderText("MM/AA")

        self.txtCVV = QLineEdit()
        self.txtCVV.setMaxLength(3)
        self.txtCVV.setPlaceholderText("CVV")
        self.txtCVV.setEchoMode(QLineEdit.Password)
        self.txtCVV.setValidator(QIntValidator(0, 999, self))

        layout.addRow("Número de tarjeta:", self.txtTarjeta)
        layout.addRow("Fecha de vencimiento:", self.txtVencimiento)
        layout.addRow("CVV:", self.txtCVV)

        self.stack.addWidget(page)

    def _update_page(self, *_args) -> None:
        is_cash = self.cmbFormaPago.currentData() == "efectivo"
        self.stack.setCurrentIndex(0 if is_cash else 1)
        if is_cash:
            self._actualizar_resumen_efectivo()

    def _actualizar_resumen_efectivo(self) -> None:
        recibido = float(self.spnEfectivo.value())
        diferencia = recibido - self.total

        if diferencia >= 0:
            cambio = diferencia
            faltante = 0.0
        else:
            cambio = 0.0
            faltante = abs(diferencia)

        self.lblCambio.setText(f"Cambio: ${cambio:.2f}")
        self.lblFaltante.setText(f"Faltante: ${faltante:.2f}")

    def _error(self, msg: str) -> None:
        QMessageBox.critical(self, "Validación", msg)

    def _validate_cash(self) -> Optional[Dict[str, Any]]:
        recibido = float(self.spnEfectivo.value())
        if recibido < self.total:
            self._error(
                f"El efectivo recibido (${recibido:.2f}) no es suficiente para cubrir el total (${self.total:.2f})."
            )
            return None

        cambio = recibido - self.total
        return {
            "forma_pago": "efectivo",
            "monto_recibido": recibido,
            "cambio": cambio,
        }

    def _validate_card(self) -> Optional[Dict[str, Any]]:
        numero = self.txtTarjeta.text().replace(" ", "").strip()
        venc = self.txtVencimiento.text().strip()
        cvv = self.txtCVV.text().strip()

        if not numero.isdigit() or len(numero) != 16:
            self._error("El número de tarjeta debe tener 16 dígitos.")
            return None

        if not re.fullmatch(r"\d{2}/\d{2}", venc):
            self._error("La fecha de vencimiento debe tener el formato MM/AA.")
            return None

        mm = int(venc[:2])
        aa = int(venc[3:])
        if mm < 1 or mm > 12:
            self._error("El mes de vencimiento no es válido.")
            return None

        current = QDate.currentDate()
        card_year = 2000 + aa
        if card_year < current.year() or (card_year == current.year() and mm < current.month()):
            self._error("La tarjeta está vencida.")
            return None

        if not cvv.isdigit() or len(cvv) != 3:
            self._error("El CVV debe tener 3 dígitos.")
            return None

        return {
            "forma_pago": "tarjeta",
            "numero_tarjeta": numero,
            "vencimiento": venc,
            "cvv": cvv,
        }

    def concretar_venta(self) -> None:
        if self.cmbFormaPago.currentData() == "efectivo":
            data = self._validate_cash()
        else:
            data = self._validate_card()

        if data is None:
            return

        self.payment_data = data
        self.accept()

    def get_payment_data(self) -> Optional[Dict[str, Any]]:
        return self.payment_data

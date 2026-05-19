from datetime import datetime
from html import escape

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QMainWindow, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QMessageBox, QInputDialog, QComboBox, QScrollArea, QWidget, QSpinBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
)

from modulos.PaletaColores import (
    BORDE, DESACTIVADO, FONDO_B, TEXTO_BOTON, SUPERFICIE,
    PRIMARIO, TEXTO, FONDO_A, BORDE_BOTON, FONDO_ACTIVO,
)
from ventanas.Reportes import (
    _VENTANA_STYLE, _BTN_PDF_STYLE, _BTN_PREVIEW_STYLE, _BTN_VOLVER_STYLE,
    _PDF_CSS, _make_tabla, _tabla_item, _guardar_pdf, _vista_previa_pdf, _fmt_money,
)

from PySide6.QtWidgets import QDialog

MAX_OPENING_AMOUNT = 999_999_999.99
DENOMINACIONES = [1000, 500, 200, 100, 50, 20, 10, 5, 1]

_IND_PENDING = (
    "background: #FEF3C7; color: #92400E; border-radius: 8px;"
    " padding: 8px; font-weight: bold;"
)
_IND_OK = (
    "background: #DCFCE7; color: #166534; border-radius: 8px;"
    " padding: 8px; font-weight: bold;"
)


def _fmt_fecha(valor):
    if valor is None:
        return "-"
    try:
        return valor.strftime("%Y-%m-%d %H:%M")
    except Exception:
        return str(valor)


def _sep() -> QFrame:
    f = QFrame()
    f.setFrameShape(QFrame.HLine)
    f.setFixedHeight(1)
    f.setStyleSheet(f"background: {BORDE}; border: none;")
    return f


def _armar_html_corte(
    vendedor_nombre: str,
    fecha_apertura,
    monto_apertura: float,
    fecha_cierre,
    total_efectivo: float,
    total_tarjeta: float,
    total_ventas: float,
    ef_declarado: float,
    tj_declarada: float,
    filas_ventas=None,
    ef_desglose=None,
    vouchers=None,
) -> str:
    """Genera HTML para el PDF de un corte de caja individual.

    ef_desglose: dict {denominacion: cantidad} con el desglose de efectivo declarado.
    vouchers: lista de [no_voucher, monto] con los vouchers de tarjeta declarados.
    """
    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    filas_html = ""
    if filas_ventas:
        for fila in filas_ventas:
            filas_html += (
                "<tr>"
                f'<td class="num">{escape(str(fila[0]))}</td>'
                f'<td class="txt">{escape(str(fila[1] or ""))}</td>'
                f'<td class="txt">{escape(str(fila[2] or ""))}</td>'
                f'<td class="num">{escape(_fmt_money(fila[3]))}</td>'
                "</tr>"
            )
    tabla_ventas = (
        '<div class="line"></div>'
        '<table class="items">'
        "<thead><tr>"
        '<th style="width:10%;text-align:right;">ID</th>'
        '<th style="width:34%;">Cliente</th>'
        '<th style="width:22%;">Forma de Pago</th>'
        '<th style="width:20%;text-align:right;">Total</th>'
        "</tr></thead>"
        f"<tbody>{filas_html}</tbody>"
        "</table>"
        if filas_ventas else ""
    )

    # ── Tabla de desglose de efectivo por denominación ──────────────────────
    tabla_ef_desglose = ""
    if ef_desglose:
        filas_denom = ""
        for denom in DENOMINACIONES:
            qty = ef_desglose.get(denom, 0)
            if qty > 0:
                subtotal = denom * qty
                filas_denom += (
                    "<tr>"
                    f'<td class="num">${denom:,}</td>'
                    f'<td class="num">{qty}</td>'
                    f'<td class="num">{escape(_fmt_money(subtotal))}</td>'
                    "</tr>"
                )
        if filas_denom:
            tabla_ef_desglose = (
                '<div class="line"></div>'
                '<p style="font-weight:bold;margin:6px 0 4px;">'
                "Desglose de Efectivo Declarado</p>"
                '<table class="items">'
                "<thead><tr>"
                '<th style="width:33%;text-align:right;">Denominaci\xf3n</th>'
                '<th style="width:33%;text-align:right;">Cantidad</th>'
                '<th style="width:33%;text-align:right;">Subtotal</th>'
                "</tr></thead>"
                f"<tbody>{filas_denom}</tbody>"
                "<tfoot><tr>"
                '<td class="num" colspan="2" style="font-weight:bold;">Total Efectivo Declarado</td>'
                f'<td class="num" style="font-weight:bold;">{escape(_fmt_money(ef_declarado))}</td>'
                "</tr></tfoot>"
                "</table>"
            )

    # ── Tabla de vouchers de tarjeta ─────────────────────────────────────────
    tabla_vouchers_html = ""
    if vouchers:
        filas_vou = ""
        for no_vou, monto in vouchers:
            filas_vou += (
                "<tr>"
                f'<td class="txt">{escape(str(no_vou))}</td>'
                f'<td class="num">{escape(_fmt_money(monto))}</td>'
                "</tr>"
            )
        if filas_vou:
            tabla_vouchers_html = (
                '<div class="line"></div>'
                '<p style="font-weight:bold;margin:6px 0 4px;">'
                "Vouchers de Tarjeta</p>"
                '<table class="items">'
                "<thead><tr>"
                '<th style="width:60%;">No. Voucher</th>'
                '<th style="width:40%;text-align:right;">Monto</th>'
                "</tr></thead>"
                f"<tbody>{filas_vou}</tbody>"
                "<tfoot><tr>"
                '<td class="txt" style="font-weight:bold;">Total Tarjeta Declarada</td>'
                f'<td class="num" style="font-weight:bold;">{escape(_fmt_money(tj_declarada))}</td>'
                "</tr></tfoot>"
                "</table>"
            )

    return (
        f"<html><head><style>{_PDF_CSS}</style></head><body>"
        '<div class="page">'
        '<div class="header">'
        '<div class="brand">GALER\xcdA DE ARTE</div>'
        '<div class="title">CORTE DE CAJA</div>'
        f'<div class="sub">Fecha: {escape(fecha_hoy)}</div>'
        "</div>"
        '<div class="line"></div>'
        '<table class="info">'
        "<tr>"
        f'<td class="label">Vendedor:</td><td class="value">{escape(vendedor_nombre)}</td>'
        f'<td class="label">Apertura:</td><td class="value">{escape(_fmt_money(monto_apertura))}</td>'
        "</tr>"
        "<tr>"
        f'<td class="label">Fecha apertura:</td><td class="value">{escape(_fmt_fecha(fecha_apertura))}</td>'
        f'<td class="label">Fecha cierre:</td><td class="value">{escape(_fmt_fecha(fecha_cierre))}</td>'
        "</tr>"
        "</table>"
        f"{tabla_ventas}"
        f"{tabla_ef_desglose}"
        f"{tabla_vouchers_html}"
        '<table class="summary">'
        f'<tr><td class="label">TOTAL EFECTIVO (ventas):</td><td class="value">{escape(_fmt_money(total_efectivo))}</td></tr>'
        f'<tr><td class="label">TOTAL TARJETA (ventas):</td><td class="value">{escape(_fmt_money(total_tarjeta))}</td></tr>'
        f'<tr><td class="label">TOTAL VENTAS:</td><td class="value">{escape(_fmt_money(total_ventas))}</td></tr>'
        '<tr><td class="label" style="padding-top:8px;border-top:1px solid #ccc;">EFECTIVO DECLARADO:</td>'
        f'<td class="value" style="padding-top:8px;border-top:1px solid #ccc;">{escape(_fmt_money(ef_declarado))}</td></tr>'
        f'<tr><td class="label">TARJETA DECLARADA:</td><td class="value">{escape(_fmt_money(tj_declarada))}</td></tr>'
        "</table>"
        '<div class="footer">Reporte generado por Sistema Galer\xeda de Arte</div>'
        "</div></body></html>"
    )


class HistorialCortesDialog(QDialog):
    """Diálogo que muestra el historial de cortes de caja."""

    def __init__(self, conexion, parent=None):
        super().__init__(parent)
        self.conexion = conexion
        self.setWindowTitle("Historial de Cortes de Caja")
        self.setMinimumSize(QSize(1000, 600))
        self.setStyleSheet(_VENTANA_STYLE)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        titulo = QLabel("Historial de Cortes de Caja")
        titulo.setAlignment(Qt.AlignHCenter)
        titulo.setFont(QFont("Segoe UI", 18, QFont.Weight.DemiBold))
        layout.addWidget(titulo)

        self.tabla = QTableWidget(0, 7)
        self.tabla.setHorizontalHeaderLabels([
            "ID", "Fecha", "Hora", "Vendedor",
            "Total Efectivo", "Total Voucher", "Total Venta",
        ])
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabla.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.setAlternatingRowColors(True)
        hdr = self.tabla.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(3, QHeaderView.Stretch)
        hdr.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        self.tabla.setMinimumHeight(350)
        layout.addWidget(self.tabla)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        btn_preview = QPushButton("Vista Previa")
        btn_preview.setCursor(Qt.PointingHandCursor)
        btn_preview.setFixedHeight(36)
        btn_preview.setFont(QFont("Segoe UI", 10))
        btn_preview.setStyleSheet(_BTN_PREVIEW_STYLE)
        btn_preview.clicked.connect(self._preview_historial)
        btn_row.addWidget(btn_preview)

        btn_descargar = QPushButton("Descargar PDF")
        btn_descargar.setCursor(Qt.PointingHandCursor)
        btn_descargar.setFixedHeight(36)
        btn_descargar.setFont(QFont("Segoe UI", 10))
        btn_descargar.setStyleSheet(_BTN_PDF_STYLE)
        btn_descargar.clicked.connect(self._exportar_historial)
        btn_row.addWidget(btn_descargar)

        btn_row.addStretch()

        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.setCursor(Qt.PointingHandCursor)
        btn_cerrar.setFixedHeight(36)
        btn_cerrar.setFont(QFont("Segoe UI", 10))
        btn_cerrar.setStyleSheet(_BTN_VOLVER_STYLE)
        btn_cerrar.clicked.connect(self.accept)
        btn_row.addWidget(btn_cerrar)

        layout.addLayout(btn_row)

        self._cargar_datos()

    def _cargar_datos(self):
        try:
            cursor = self.conexion.cursor()
            cursor.execute(
                """
                SELECT cc.id_cierre, cc.fecha, v.nombre, cc.id_vendedor,
                       cc.totalEfectivo, cc.totalVoucher, cc.montoTotal
                FROM CierreCaja cc
                LEFT JOIN Vendedores v ON v.id_vendedor = cc.id_vendedor
                ORDER BY cc.fecha DESC
                """
            )
            rows = cursor.fetchall()
            self.tabla.setRowCount(0)
            self._cortes = []
            for fila in rows:
                id_cierre = int(fila[0])
                fecha_dt = fila[1]
                fecha_str = str(fecha_dt)[:10] if fecha_dt else "-"
                s = str(fecha_dt) if fecha_dt else ""
                hora_str = s[11:19] if len(s) >= 19 else (s[11:] if len(s) > 10 else "-")
                vendedor = str(fila[2]) if fila[2] else "-"
                id_vendedor = int(fila[3]) if fila[3] is not None else None
                ef = float(fila[4] or 0)
                vou = float(fila[5] or 0)
                total = float(fila[6] or 0)

                # Fetch apertura info for this vendor on the cierre date
                apertura_fecha = None
                apertura_monto = 0.0
                if id_vendedor is not None and fecha_dt is not None:
                    try:
                        cur2 = self.conexion.cursor()
                        cur2.execute(
                            """
                            SELECT monto, fecha FROM AperturaCaja
                            WHERE id_vendedor = ?
                              AND DATE(fecha) = DATE(?)
                            ORDER BY id_apertura DESC
                            LIMIT 1
                            """,
                            (id_vendedor, fecha_dt),
                        )
                        ap = cur2.fetchone()
                        if ap:
                            apertura_monto = float(ap[0] or 0)
                            apertura_fecha = ap[1]
                    except Exception:
                        pass

                self._cortes.append({
                    "id_cierre": id_cierre,
                    "fecha_dt": fecha_dt,
                    "fecha_str": fecha_str,
                    "hora_str": hora_str,
                    "vendedor": vendedor,
                    "ef": ef,
                    "vou": vou,
                    "total": total,
                    "apertura_fecha": apertura_fecha,
                    "apertura_monto": apertura_monto,
                })
                row_idx = self.tabla.rowCount()
                self.tabla.insertRow(row_idx)
                for col, val in enumerate([
                    str(id_cierre), fecha_str, hora_str, vendedor,
                    _fmt_money(ef), _fmt_money(vou), _fmt_money(total),
                ]):
                    it = _tabla_item(
                        val,
                        Qt.AlignRight | Qt.AlignVCenter if col in (0, 4, 5, 6) else Qt.AlignLeft | Qt.AlignVCenter,
                    )
                    self.tabla.setItem(row_idx, col, it)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo cargar el historial:\n{e}")

    def _get_html(self, idx: int) -> str:
        corte = self._cortes[idx]
        return _armar_html_corte(
            vendedor_nombre=corte["vendedor"],
            fecha_apertura=corte["apertura_fecha"],
            monto_apertura=corte["apertura_monto"],
            fecha_cierre=corte["fecha_dt"],
            total_efectivo=corte["ef"],
            total_tarjeta=corte["vou"],
            total_ventas=corte["total"],
            ef_declarado=corte["ef"],
            tj_declarada=corte["vou"],
        )

    def _preview(self, idx: int):
        corte = self._cortes[idx]
        nombre_arch = f"corte_caja_{corte['id_cierre']}.pdf"
        _vista_previa_pdf(self, "Corte de Caja", nombre_arch, self._get_html(idx))

    def _exportar(self, idx: int):
        corte = self._cortes[idx]
        nombre_arch = f"corte_caja_{corte['id_cierre']}.pdf"
        _guardar_pdf(self, "Corte de Caja", nombre_arch, self._get_html(idx))

    def _get_html_historial(self) -> str:
        fecha_hoy = datetime.now().strftime("%Y-%m-%d")
        filas_html = ""
        for corte in self._cortes:
            filas_html += (
                "<tr>"
                f'<td class="num">{escape(corte["fecha_str"])}</td>'
                f'<td class="num">{escape(corte["hora_str"])}</td>'
                f'<td class="txt">{escape(corte["vendedor"])}</td>'
                f'<td class="num">{escape(_fmt_money(corte["ef"]))}</td>'
                f'<td class="num">{escape(_fmt_money(corte["vou"]))}</td>'
                f'<td class="num">{escape(_fmt_money(corte["total"]))}</td>'
                "</tr>"
            )
        return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
{_PDF_CSS}
</style>
</head>
<body>
<div class="header">
  <div class="brand">Galería de Arte</div>
  <div class="title">Historial de Cortes de Caja</div>
  <div class="sub">Generado el {fecha_hoy}</div>
</div>
<div class="line"></div>
<table class="items">
  <thead><tr>
    <th style="width:12%;text-align:right;">Fecha</th>
    <th style="width:10%;text-align:right;">Hora</th>
    <th style="width:28%;">Vendedor</th>
    <th style="width:16%;text-align:right;">Total Efectivo</th>
    <th style="width:16%;text-align:right;">Total Voucher</th>
    <th style="width:18%;text-align:right;">Total Venta</th>
  </tr></thead>
  <tbody>{filas_html}</tbody>
</table>
<div class="footer">Sistema Galería de Arte &mdash; Historial de Cortes</div>
</body>
</html>"""

    def _preview_historial(self):
        if not self._cortes:
            QMessageBox.information(self, "Sin datos", "No hay registros en el historial.")
            return
        _vista_previa_pdf(self, "Historial de Cortes de Caja", "historial_cortes.pdf",
                          self._get_html_historial())

    def _exportar_historial(self):
        if not self._cortes:
            QMessageBox.information(self, "Sin datos", "No hay registros en el historial.")
            return
        _guardar_pdf(self, "Historial de Cortes de Caja", "historial_cortes.pdf",
                     self._get_html_historial())


class CorteCajaVentana(QMainWindow):
    def __init__(self, conexion, ventana_padre=None):
        super().__init__(ventana_padre)
        self.conexion = conexion
        self.ventana_padre = ventana_padre

        # ── state ──────────────────────────────────────────────────────────
        self._id_vendedor = None
        self._id_apertura = None
        self._monto_apertura = 0.0
        self._fecha_apertura = None
        self._total_ventas = 0.0
        self._total_efectivo = 0.0
        self._total_tarjeta = 0.0
        self._datos_ventas = []

        self.setWindowTitle("Corte de Caja")
        self.setMinimumSize(QSize(1100, 820))
        self.setStyleSheet(_VENTANA_STYLE)

        # ── root + scroll ──────────────────────────────────────────────────
        root = QWidget()
        root.setStyleSheet(f"background: {FONDO_A};")
        self.setCentralWidget(root)

        outer = QVBoxLayout(root)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        outer.addWidget(scroll)

        page = QWidget()
        page.setStyleSheet(f"background: {FONDO_A};")
        scroll.setWidget(page)

        content = QVBoxLayout(page)
        content.setContentsMargins(36, 28, 36, 28)
        content.setSpacing(14)

        # ── title ──────────────────────────────────────────────────────────
        titulo = QLabel("Corte de Caja")
        titulo.setAlignment(Qt.AlignHCenter)
        titulo.setFont(QFont("Segoe UI", 24, QFont.Weight.DemiBold))
        content.addWidget(titulo)

        subtitulo = QLabel("Gestión de apertura y cierre de caja por vendedor")
        subtitulo.setAlignment(Qt.AlignHCenter)
        subtitulo.setFont(QFont("Segoe UI", 11))
        subtitulo.setStyleSheet(f"color: {DESACTIVADO};")
        content.addWidget(subtitulo)

        content.addWidget(_sep())

        # ── vendor selector row ────────────────────────────────────────────
        vend_row = QHBoxLayout()
        vend_row.setSpacing(12)

        lbl_v = QLabel("Vendedor:")
        lbl_v.setFont(QFont("Segoe UI", 12, QFont.Weight.DemiBold))
        vend_row.addWidget(lbl_v)

        self.cmb_vendedores = QComboBox()
        self.cmb_vendedores.setMinimumWidth(240)
        self.cmb_vendedores.setFixedHeight(38)
        self.cmb_vendedores.setFont(QFont("Segoe UI", 11))
        vend_row.addWidget(self.cmb_vendedores)

        self.btn_aperturar = QPushButton("\U0001f513 Aperturar Caja")
        self.btn_aperturar.setCursor(Qt.PointingHandCursor)
        self.btn_aperturar.setFixedHeight(38)
        self.btn_aperturar.setFont(QFont("Segoe UI", 10, QFont.Weight.DemiBold))
        self.btn_aperturar.setStyleSheet(_BTN_PDF_STYLE)
        self.btn_aperturar.setEnabled(False)
        self.btn_aperturar.clicked.connect(self._aperturar_caja)
        vend_row.addWidget(self.btn_aperturar)

        self.lbl_apertura_info = QLabel("")
        self.lbl_apertura_info.setFont(QFont("Segoe UI", 11))
        vend_row.addWidget(self.lbl_apertura_info)
        vend_row.addStretch(1)
        content.addLayout(vend_row)

        content.addWidget(_sep())

        # ── sales table ────────────────────────────────────────────────────
        lbl_ventas = QLabel("Ventas del Día")
        lbl_ventas.setFont(QFont("Segoe UI", 14, QFont.Weight.DemiBold))
        content.addWidget(lbl_ventas)

        self.tabla = _make_tabla(["ID", "Cliente", "Forma de Pago", "Total"], min_height=160)
        content.addWidget(self.tabla)

        sum_row = QHBoxLayout()
        sum_row.addStretch(1)
        self.lbl_ef_vtas = self._badge("Efectivo: $0.00")
        self.lbl_tj_vtas = self._badge("Tarjeta: $0.00")
        self.lbl_total_vtas = self._badge("Total: $0.00")
        for w in (self.lbl_ef_vtas, self.lbl_tj_vtas, self.lbl_total_vtas):
            sum_row.addWidget(w)
            sum_row.addSpacing(8)
        content.addLayout(sum_row)

        # ── declaration section ────────────────────────────────────────────
        self.decl_widget = QWidget()
        decl_lay = QVBoxLayout(self.decl_widget)
        decl_lay.setContentsMargins(0, 0, 0, 0)
        decl_lay.setSpacing(14)

        decl_lay.addWidget(_sep())

        decl_titulo = QLabel("Declaración para Cierre de Caja")
        decl_titulo.setFont(QFont("Segoe UI", 16, QFont.Weight.DemiBold))
        decl_lay.addWidget(decl_titulo)

        decl_cols = QHBoxLayout()
        decl_cols.setSpacing(20)

        self._spinboxes = {}
        self._sub_labels = {}

        decl_cols.addWidget(self._make_ef_card())
        decl_cols.addWidget(self._make_tj_card())
        decl_lay.addLayout(decl_cols)

        content.addWidget(self.decl_widget)
        self.decl_widget.setVisible(False)

        content.addWidget(_sep())

        # ── action buttons ─────────────────────────────────────────────────
        acc = QHBoxLayout()
        acc.addStretch(1)

        self.btn_preview = QPushButton("Vista Previa")
        self.btn_preview.setCursor(Qt.PointingHandCursor)
        self.btn_preview.setFixedHeight(40)
        self.btn_preview.setFont(QFont("Segoe UI", 11, QFont.Weight.DemiBold))
        self.btn_preview.setStyleSheet(_BTN_PREVIEW_STYLE)
        self.btn_preview.setEnabled(False)
        self.btn_preview.clicked.connect(self.vista_previa_pdf)

        self.btn_pdf = QPushButton("Exportar PDF")
        self.btn_pdf.setCursor(Qt.PointingHandCursor)
        self.btn_pdf.setFixedHeight(40)
        self.btn_pdf.setFont(QFont("Segoe UI", 11, QFont.Weight.DemiBold))
        self.btn_pdf.setStyleSheet(_BTN_PDF_STYLE)
        self.btn_pdf.setEnabled(False)
        self.btn_pdf.clicked.connect(self.exportar_pdf)

        self.btn_cerrar_caja = QPushButton("\U0001f512 Cerrar Caja")
        self.btn_cerrar_caja.setCursor(Qt.PointingHandCursor)
        self.btn_cerrar_caja.setFixedHeight(40)
        self.btn_cerrar_caja.setFont(QFont("Segoe UI", 11, QFont.Weight.DemiBold))
        self.btn_cerrar_caja.setStyleSheet(_BTN_PDF_STYLE)
        self.btn_cerrar_caja.setEnabled(False)

        btn_historial = QPushButton("\U0001f4cb Historial de Cortes")
        btn_historial.setCursor(Qt.PointingHandCursor)
        btn_historial.setFixedHeight(40)
        btn_historial.setFont(QFont("Segoe UI", 11, QFont.Weight.DemiBold))
        btn_historial.setStyleSheet(_BTN_PREVIEW_STYLE)
        btn_historial.clicked.connect(self._ver_historial)

        btn_volver = QPushButton("Volver")
        btn_volver.setCursor(Qt.PointingHandCursor)
        btn_volver.setFixedHeight(40)
        btn_volver.setFont(QFont("Segoe UI", 11))
        btn_volver.setStyleSheet(_BTN_VOLVER_STYLE)
        btn_volver.clicked.connect(self.regresar)

        for w in (self.btn_preview, self.btn_pdf, self.btn_cerrar_caja, btn_historial, btn_volver):
            acc.addWidget(w)
            acc.addSpacing(8)
        content.addLayout(acc)

        content.addStretch(1)

        # ── initial load ───────────────────────────────────────────────────
        self._cargar_vendedores()
        self.cmb_vendedores.currentIndexChanged.connect(self._on_vendedor_changed)

    # ── widget helpers ─────────────────────────────────────────────────────

    def _badge(self, text):
        lbl = QLabel(text)
        lbl.setFont(QFont("Segoe UI", 11, QFont.Weight.DemiBold))
        lbl.setStyleSheet(
            f"color: {TEXTO_BOTON}; background: {FONDO_B}; border: 1px solid {BORDE};"
            " border-radius: 8px; padding: 6px 10px;"
        )
        return lbl

    def _make_ef_card(self):
        card = QFrame()
        card.setObjectName("efCard")
        card.setStyleSheet(
            f"QFrame#efCard {{ background: {SUPERFICIE}; border: 1px solid {BORDE};"
            " border-radius: 10px; }"
        )
        lay = QVBoxLayout(card)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(8)

        lbl_t = QLabel("\U0001f4b5 Declaración de Efectivo")
        lbl_t.setFont(QFont("Segoe UI", 13, QFont.Weight.DemiBold))
        lay.addWidget(lbl_t)

        self.lbl_meta_ef = QLabel("Meta: $0.00")
        self.lbl_meta_ef.setFont(QFont("Segoe UI", 10))
        self.lbl_meta_ef.setStyleSheet(f"color: {DESACTIVADO};")
        lay.addWidget(self.lbl_meta_ef)

        spin_style = (
            f"QSpinBox {{ background: {SUPERFICIE}; border: 1px solid {BORDE_BOTON};"
            f" border-radius: 6px; padding: 3px 6px; color: {TEXTO}; }}"
        )
        for denom in DENOMINACIONES:
            row = QHBoxLayout()

            ld = QLabel(f"${denom:,}")
            ld.setFont(QFont("Segoe UI", 11))
            ld.setFixedWidth(68)
            row.addWidget(ld)

            spin = QSpinBox()
            spin.setRange(0, 99999)
            spin.setFixedHeight(30)
            spin.setFixedWidth(84)
            spin.setFont(QFont("Segoe UI", 11))
            spin.setStyleSheet(spin_style)
            spin.valueChanged.connect(lambda _v, d=denom: self._on_denom_changed(d))
            row.addWidget(spin)

            leq = QLabel("=")
            leq.setFont(QFont("Segoe UI", 11))
            leq.setContentsMargins(4, 0, 4, 0)
            row.addWidget(leq)

            lsub = QLabel("$0.00")
            lsub.setFont(QFont("Segoe UI", 11))
            lsub.setFixedWidth(96)
            lsub.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            row.addWidget(lsub)
            row.addStretch(1)

            lay.addLayout(row)
            self._spinboxes[denom] = spin
            self._sub_labels[denom] = lsub

        isep = QFrame()
        isep.setFrameShape(QFrame.HLine)
        isep.setFixedHeight(1)
        isep.setStyleSheet(f"background: {BORDE}; border: none;")
        lay.addWidget(isep)

        tot_row = QHBoxLayout()
        tot_row.addStretch(1)
        lt = QLabel("Total declarado:")
        lt.setFont(QFont("Segoe UI", 11, QFont.Weight.DemiBold))
        tot_row.addWidget(lt)
        self.lbl_ef_declarado = QLabel("$0.00")
        self.lbl_ef_declarado.setFont(QFont("Segoe UI", 12, QFont.Weight.DemiBold))
        self.lbl_ef_declarado.setMinimumWidth(100)
        self.lbl_ef_declarado.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        tot_row.addWidget(self.lbl_ef_declarado)
        lay.addLayout(tot_row)

        self.lbl_ind_ef = QLabel("Falta: $0.00")
        self.lbl_ind_ef.setFont(QFont("Segoe UI", 12, QFont.Weight.DemiBold))
        self.lbl_ind_ef.setAlignment(Qt.AlignCenter)
        self.lbl_ind_ef.setStyleSheet(_IND_PENDING)
        lay.addWidget(self.lbl_ind_ef)

        return card

    def _make_tj_card(self):
        card = QFrame()
        card.setObjectName("tjCard")
        card.setStyleSheet(
            f"QFrame#tjCard {{ background: {SUPERFICIE}; border: 1px solid {BORDE};"
            " border-radius: 10px; }"
        )
        lay = QVBoxLayout(card)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(8)

        lbl_t = QLabel("\U0001f4b3 Declaración de Tarjeta / Vouchers")
        lbl_t.setFont(QFont("Segoe UI", 13, QFont.Weight.DemiBold))
        lay.addWidget(lbl_t)

        self.lbl_meta_tj = QLabel("Meta: $0.00")
        self.lbl_meta_tj.setFont(QFont("Segoe UI", 10))
        self.lbl_meta_tj.setStyleSheet(f"color: {DESACTIVADO};")
        lay.addWidget(self.lbl_meta_tj)

        self.tabla_vouchers = QTableWidget(1, 2)
        self.tabla_vouchers.setHorizontalHeaderLabels(["No. Voucher", "Monto"])
        hdr = self.tabla_vouchers.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.Stretch)
        hdr.setSectionResizeMode(1, QHeaderView.Fixed)
        self.tabla_vouchers.setColumnWidth(1, 130)
        self.tabla_vouchers.verticalHeader().setVisible(False)
        self.tabla_vouchers.setMinimumHeight(240)
        self.tabla_vouchers.setAlternatingRowColors(True)
        self.tabla_vouchers.itemChanged.connect(self._on_voucher_changed)
        lay.addWidget(self.tabla_vouchers)

        isep = QFrame()
        isep.setFrameShape(QFrame.HLine)
        isep.setFixedHeight(1)
        isep.setStyleSheet(f"background: {BORDE}; border: none;")
        lay.addWidget(isep)

        tot_row = QHBoxLayout()
        tot_row.addStretch(1)
        lt = QLabel("Total declarado:")
        lt.setFont(QFont("Segoe UI", 11, QFont.Weight.DemiBold))
        tot_row.addWidget(lt)
        self.lbl_tj_declarada = QLabel("$0.00")
        self.lbl_tj_declarada.setFont(QFont("Segoe UI", 12, QFont.Weight.DemiBold))
        self.lbl_tj_declarada.setMinimumWidth(100)
        self.lbl_tj_declarada.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        tot_row.addWidget(self.lbl_tj_declarada)
        lay.addLayout(tot_row)

        self.lbl_ind_tj = QLabel("Falta: $0.00")
        self.lbl_ind_tj.setFont(QFont("Segoe UI", 12, QFont.Weight.DemiBold))
        self.lbl_ind_tj.setAlignment(Qt.AlignCenter)
        self.lbl_ind_tj.setStyleSheet(_IND_PENDING)
        lay.addWidget(self.lbl_ind_tj)

        return card

    # ── data loading ───────────────────────────────────────────────────────

    def _cargar_vendedores(self):
        try:
            cursor = self.conexion.cursor()
            cursor.execute(
                "SELECT id_vendedor, nombre FROM Vendedores WHERE activo = 1 ORDER BY nombre"
            )
            rows = cursor.fetchall()
            self.cmb_vendedores.blockSignals(True)
            self.cmb_vendedores.clear()
            self.cmb_vendedores.addItem("-- Seleccionar vendedor --", None)
            for r in rows:
                self.cmb_vendedores.addItem(str(r[1]), int(r[0]))
            self.cmb_vendedores.blockSignals(False)
        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"No se pudo cargar la lista de vendedores:\n{e}"
            )

    def _on_vendedor_changed(self, _index):
        self._id_vendedor = self.cmb_vendedores.currentData()
        if self._id_vendedor is None:
            self._limpiar_todo()
            return
        self._reset_declaracion()
        self.recargar()

    def _limpiar_todo(self):
        self.tabla.setRowCount(0)
        self._datos_ventas = []
        self._total_ventas = self._total_efectivo = self._total_tarjeta = 0.0
        self.lbl_ef_vtas.setText("Efectivo: $0.00")
        self.lbl_tj_vtas.setText("Tarjeta: $0.00")
        self.lbl_total_vtas.setText("Total: $0.00")
        self.lbl_apertura_info.setText("")
        self.btn_aperturar.setEnabled(False)
        self.btn_aperturar.setText("\U0001f513 Aperturar Caja")
        self.decl_widget.setVisible(False)
        self.btn_pdf.setEnabled(False)
        self.btn_preview.setEnabled(False)
        self.btn_cerrar_caja.setEnabled(False)
        self.btn_cerrar_caja.setText("\U0001f512 Cerrar Caja")
        self.btn_cerrar_caja.setStyleSheet(_BTN_PDF_STYLE)

    def _reset_declaracion(self):
        for denom, spin in self._spinboxes.items():
            spin.blockSignals(True)
            spin.setValue(0)
            spin.blockSignals(False)
            self._sub_labels[denom].setText("$0.00")
        self.tabla_vouchers.blockSignals(True)
        self.tabla_vouchers.setRowCount(1)
        self.tabla_vouchers.clearContents()
        self.tabla_vouchers.blockSignals(False)
        self.lbl_ef_declarado.setText("$0.00")
        self.lbl_tj_declarada.setText("$0.00")
        self.lbl_ind_ef.setText("Falta: $0.00")
        self.lbl_ind_ef.setStyleSheet(_IND_PENDING)
        self.lbl_ind_tj.setText("Falta: $0.00")
        self.lbl_ind_tj.setStyleSheet(_IND_PENDING)

    def _apertura_hoy(self):
        if self._id_vendedor is None:
            return None
        cursor = self.conexion.cursor()
        cursor.execute(
            """
            SELECT id_apertura, monto, fecha
            FROM AperturaCaja
            WHERE id_vendedor = ?
              AND DATE(fecha) = DATE('now')
            ORDER BY id_apertura DESC
            LIMIT 1
            """,
            (self._id_vendedor,),
        )
        return cursor.fetchone()

    def _caja_cerrada_hoy(self):
        if self._id_vendedor is None:
            return False
        try:
            cursor = self.conexion.cursor()
            cursor.execute(
                """
                SELECT COUNT(1)
                FROM CierreCaja
                WHERE id_vendedor = ?
                  AND DATE(fecha) = DATE('now')
                """,
                (self._id_vendedor,),
            )
            row = cursor.fetchone()
            return bool(row and row[0])
        except Exception:
            return False

    def recargar(self):
        if self._id_vendedor is None:
            self._limpiar_todo()
            return
        try:
            apertura = self._apertura_hoy()
            tiene_apertura = apertura is not None
            self._id_apertura = apertura[0] if apertura else None
            self._monto_apertura = float((apertura[1] if apertura else 0) or 0)
            self._fecha_apertura = apertura[2] if apertura else None

            if tiene_apertura:
                self.lbl_apertura_info.setText(
                    f"\u2713 Aperturada: {_fmt_money(self._monto_apertura)}"
                    f"  |  {_fmt_fecha(self._fecha_apertura)}"
                )
                self.lbl_apertura_info.setStyleSheet("color: #166534; font-weight: bold;")
                self.btn_aperturar.setEnabled(False)
                self.btn_aperturar.setText("\u2713 Caja Aperturada")
            else:
                self.lbl_apertura_info.setText("Sin apertura hoy")
                self.lbl_apertura_info.setStyleSheet(f"color: {DESACTIVADO};")
                self.btn_aperturar.setEnabled(True)
                self.btn_aperturar.setText("\U0001f513 Aperturar Caja")

            cursor = self.conexion.cursor()
            cursor.execute(
                """
                SELECT v.id_venta, c.nombre AS cliente, v.forma_pago, v.total
                FROM Ventas v
                LEFT JOIN Clientes c ON c.id_cliente = v.id_cliente
                WHERE v.id_vendedor = ?
                  AND DATE(v.fecha) = DATE('now')
                ORDER BY v.fecha
                """,
                (self._id_vendedor,),
            )
            filas = cursor.fetchall()
            self._datos_ventas = filas

            self.tabla.setRowCount(0)
            self._total_ventas = self._total_efectivo = self._total_tarjeta = 0.0
            for fila in filas:
                row = self.tabla.rowCount()
                self.tabla.insertRow(row)
                valores = [
                    fila[0],
                    fila[1] or "",
                    fila[2] or "",
                    _fmt_money(fila[3]),
                ]
                aligns = [
                    Qt.AlignRight | Qt.AlignVCenter,
                    Qt.AlignLeft | Qt.AlignVCenter,
                    Qt.AlignLeft | Qt.AlignVCenter,
                    Qt.AlignRight | Qt.AlignVCenter,
                ]
                for col, (val, al) in enumerate(zip(valores, aligns)):
                    self.tabla.setItem(row, col, _tabla_item(val, al))
                monto = float(fila[3] or 0)
                self._total_ventas += monto
                fp = (fila[2] or "").lower().strip()
                if fp == "efectivo":
                    self._total_efectivo += monto
                elif fp == "tarjeta":
                    self._total_tarjeta += monto

            self.lbl_ef_vtas.setText(f"Efectivo: {_fmt_money(self._total_efectivo)}")
            self.lbl_tj_vtas.setText(f"Tarjeta: {_fmt_money(self._total_tarjeta)}")
            self.lbl_total_vtas.setText(f"Total: {_fmt_money(self._total_ventas)}")

            hay_datos = bool(self._datos_ventas)
            self.btn_pdf.setEnabled(hay_datos and tiene_apertura)
            self.btn_preview.setEnabled(hay_datos and tiene_apertura)

            cerrada = self._caja_cerrada_hoy()
            if tiene_apertura and not cerrada:
                self.decl_widget.setVisible(True)
                self.lbl_meta_ef.setText(f"Meta: {_fmt_money(self._total_efectivo)}")
                self.lbl_meta_tj.setText(f"Meta: {_fmt_money(self._total_tarjeta)}")
                self._actualizar_indicadores()
            else:
                self.decl_widget.setVisible(False)

            try:
                self.btn_cerrar_caja.clicked.disconnect()
            except Exception:
                pass
            if cerrada:
                self.btn_cerrar_caja.setText("\U0001f513 Reabrir Caja")
                self.btn_cerrar_caja.setStyleSheet(_BTN_PREVIEW_STYLE)
                self.btn_cerrar_caja.setEnabled(True)
                self.btn_cerrar_caja.clicked.connect(self._reabrir_caja)
            elif tiene_apertura:
                self.btn_cerrar_caja.setText("\U0001f512 Cerrar Caja")
                self.btn_cerrar_caja.setStyleSheet(_BTN_PDF_STYLE)
                self.btn_cerrar_caja.clicked.connect(self._cerrar_caja)
                self._actualizar_btn_cerrar()
            else:
                self.btn_cerrar_caja.setText("\U0001f512 Cerrar Caja")
                self.btn_cerrar_caja.setStyleSheet(_BTN_PDF_STYLE)
                self.btn_cerrar_caja.setEnabled(False)

        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"No se pudo cargar el corte de caja:\n{e}"
            )

    # ── apertura ───────────────────────────────────────────────────────────

    def _aperturar_caja(self):
        if self._id_vendedor is None:
            return
        monto, ok = QInputDialog.getDouble(
            self,
            "Apertura de Caja",
            "Monto inicial de apertura:",
            0.0,
            0.0,
            MAX_OPENING_AMOUNT,
            2,
        )
        if not ok:
            return
        try:
            cursor = self.conexion.cursor()
            cursor.execute(
                """
                INSERT INTO AperturaCaja (id_vendedor, monto, fecha)
                SELECT ?, ?, datetime('now', 'localtime')
                WHERE NOT EXISTS (
                    SELECT 1 FROM AperturaCaja
                    WHERE id_vendedor = ?
                      AND DATE(fecha) = DATE('now', 'localtime')
                )
                """,
                (self._id_vendedor, monto, self._id_vendedor),
            )
            filas = cursor.rowcount
            self.conexion.commit()
            if filas == 0:
                QMessageBox.warning(
                    self,
                    "Aviso",
                    "Ya existe una apertura de caja para este vendedor hoy.",
                )
            else:
                QMessageBox.information(self, "Listo", "Caja aperturada correctamente.")
            self.recargar()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo aperturar la caja:\n{e}")

    # ── declaration helpers ────────────────────────────────────────────────

    def _on_denom_changed(self, denom):
        qty = self._spinboxes[denom].value()
        self._sub_labels[denom].setText(_fmt_money(denom * qty))
        self._actualizar_indicadores()

    def _get_ef_declarado(self):
        return sum(d * self._spinboxes[d].value() for d in DENOMINACIONES)

    def _get_tj_declarada(self):
        total = 0.0
        for row in range(self.tabla_vouchers.rowCount()):
            item = self.tabla_vouchers.item(row, 1)
            if item:
                txt = item.text().strip().replace(",", "").replace("$", "")
                if txt:
                    try:
                        val = float(txt)
                        if val > 0:
                            total += val
                    except ValueError:
                        pass
        return total

    def _actualizar_indicadores(self):
        ef = self._get_ef_declarado()
        tj = self._get_tj_declarada()

        self.lbl_ef_declarado.setText(_fmt_money(ef))
        falta_ef = self._total_efectivo - ef
        if falta_ef <= 0:
            self.lbl_ind_ef.setText("\u2713 Monto completado")
            self.lbl_ind_ef.setStyleSheet(_IND_OK)
        else:
            self.lbl_ind_ef.setText(f"Falta: {_fmt_money(falta_ef)}")
            self.lbl_ind_ef.setStyleSheet(_IND_PENDING)

        self.lbl_tj_declarada.setText(_fmt_money(tj))
        falta_tj = self._total_tarjeta - tj
        if falta_tj <= 0:
            self.lbl_ind_tj.setText("\u2713 Monto completado")
            self.lbl_ind_tj.setStyleSheet(_IND_OK)
        else:
            self.lbl_ind_tj.setText(f"Falta: {_fmt_money(falta_tj)}")
            self.lbl_ind_tj.setStyleSheet(_IND_PENDING)

        self._actualizar_btn_cerrar()

    def _actualizar_btn_cerrar(self):
        ef = self._get_ef_declarado()
        tj = self._get_tj_declarada()
        ef_ok = self._total_efectivo <= 0 or ef >= self._total_efectivo
        tj_ok = self._total_tarjeta <= 0 or tj >= self._total_tarjeta
        if "Cerrar" in self.btn_cerrar_caja.text():
            self.btn_cerrar_caja.setEnabled(ef_ok and tj_ok)

    def _on_voucher_changed(self, item):
        if item is None:
            return
        row = item.row()
        total_rows = self.tabla_vouchers.rowCount()
        if row == total_rows - 1:
            item_voucher = self.tabla_vouchers.item(row, 0)
            item_monto = self.tabla_vouchers.item(row, 1)
            has_content = (item_voucher and item_voucher.text().strip()) or (
                item_monto and item_monto.text().strip()
            )
            if has_content:
                self.tabla_vouchers.blockSignals(True)
                self.tabla_vouchers.insertRow(total_rows)
                self.tabla_vouchers.blockSignals(False)
        self._actualizar_indicadores()

    # ── cerrar / reabrir ───────────────────────────────────────────────────

    def _cerrar_caja(self):
        if self._id_vendedor is None:
            return
        ef_decl = self._get_ef_declarado()
        tj_decl = self._get_tj_declarada()
        monto_total = self._monto_apertura + ef_decl + tj_decl

        respuesta = QMessageBox.question(
            self,
            "Confirmar cierre de caja",
            f"Vendedor: {self.cmb_vendedores.currentText()}\n"
            f"Monto apertura:     {_fmt_money(self._monto_apertura)}\n"
            f"Efectivo declarado: {_fmt_money(ef_decl)}\n"
            f"Tarjeta declarada:  {_fmt_money(tj_decl)}\n"
            f"Monto total:        {_fmt_money(monto_total)}\n\n"
            "\xbfDeseas continuar?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if respuesta != QMessageBox.Yes:
            return
        try:
            cursor = self.conexion.cursor()
            cursor.execute(
                """
                INSERT INTO CierreCaja
                    (id_vendedor, fecha, totalEfectivo, totalVoucher, montoTotal)
                SELECT ?, datetime('now', 'localtime'), ?, ?, ?
                WHERE NOT EXISTS (
                    SELECT 1 FROM CierreCaja
                    WHERE id_vendedor = ?
                      AND DATE(fecha) = DATE('now', 'localtime')
                )
                """,
                (self._id_vendedor, ef_decl, tj_decl, monto_total, self._id_vendedor),
            )
            filas = cursor.rowcount
            if filas == 0:
                QMessageBox.warning(
                    self,
                    "Aviso",
                    "Ya existe un cierre de caja para este vendedor hoy.",
                )
                return
            self.conexion.commit()
            QMessageBox.information(
                self, "Listo", "Cierre de caja registrado correctamente."
            )
            self._reset_declaracion()
            self.recargar()
        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"No se pudo registrar el cierre de caja:\n{e}"
            )

    def _reabrir_caja(self):
        if self._id_vendedor is None:
            return
        respuesta = QMessageBox.question(
            self,
            "Confirmar reapertura de caja",
            f"Se eliminar\xe1 el cierre de caja del vendedor "
            f"'{self.cmb_vendedores.currentText()}' de hoy.\n\xbfDeseas continuar?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if respuesta != QMessageBox.Yes:
            return
        try:
            cursor = self.conexion.cursor()
            cursor.execute(
                """
                DELETE FROM CierreCaja
                WHERE id_cierre = (
                    SELECT id_cierre
                    FROM CierreCaja
                    WHERE id_vendedor = ?
                      AND DATE(fecha) = DATE('now', 'localtime')
                    ORDER BY fecha DESC
                    LIMIT 1
                )
                """,
                (self._id_vendedor,),
            )
            self.conexion.commit()
            QMessageBox.information(
                self, "Listo", "La caja ha sido reabierta correctamente."
            )
            self.recargar()
        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"No se pudo reabrir la caja:\n{e}"
            )

    # ── PDF ────────────────────────────────────────────────────────────────

    def _armar_html(self):
        ef_declarado = self._get_ef_declarado()
        tj_declarada = self._get_tj_declarada()

        # Desglose de efectivo: {denominacion: cantidad} (omitir ceros)
        ef_desglose = {
            d: self._spinboxes[d].value()
            for d in DENOMINACIONES
            if self._spinboxes[d].value() > 0
        }

        # Lista de vouchers: [[no_voucher, monto], ...] (solo filas con monto > 0)
        vouchers = []
        for row in range(self.tabla_vouchers.rowCount()):
            item_vou = self.tabla_vouchers.item(row, 0)
            item_monto = self.tabla_vouchers.item(row, 1)
            no_vou = item_vou.text().strip() if item_vou else ""
            monto_txt = item_monto.text().strip().replace(",", "").replace("$", "") if item_monto else ""
            if monto_txt:
                try:
                    monto = float(monto_txt)
                    if monto > 0:
                        vouchers.append([no_vou or "-", monto])
                except ValueError:
                    pass

        return _armar_html_corte(
            vendedor_nombre=self.cmb_vendedores.currentText(),
            fecha_apertura=self._fecha_apertura,
            monto_apertura=self._monto_apertura,
            fecha_cierre=None,
            total_efectivo=self._total_efectivo,
            total_tarjeta=self._total_tarjeta,
            total_ventas=self._total_ventas,
            ef_declarado=ef_declarado,
            tj_declarada=tj_declarada,
            filas_ventas=self._datos_ventas,
            ef_desglose=ef_desglose,
            vouchers=vouchers,
        )

    def exportar_pdf(self):
        fecha_hoy = datetime.now().strftime("%Y%m%d")
        _guardar_pdf(
            self,
            "Corte de Caja",
            f"corte_caja_{fecha_hoy}.pdf",
            self._armar_html(),
        )

    def vista_previa_pdf(self):
        fecha_hoy = datetime.now().strftime("%Y%m%d")
        _vista_previa_pdf(
            self,
            "Corte de Caja",
            f"corte_caja_{fecha_hoy}.pdf",
            self._armar_html(),
        )

    def _ver_historial(self):
        dlg = HistorialCortesDialog(self.conexion, self)
        dlg.exec()

    # ── navigation ─────────────────────────────────────────────────────────

    def regresar(self):
        if self.ventana_padre:
            self.ventana_padre.show()
        self.close()

    def closeEvent(self, event):
        if self.ventana_padre is not None:
            self.ventana_padre.ventana_corte_caja = None
            self.ventana_padre.show()
            self.ventana_padre.raise_()
            self.ventana_padre.activateWindow()
        super().closeEvent(event)

"""
Pruebas unitarias para las validaciones de campos de formulario.

Valida las mismas expresiones regulares usadas en las ventanas (QRegularExpressionValidator)
y la lógica de validación de tarjeta y fechas de Exhibiciones.
"""

import re
import unittest
from datetime import date

# ---------------------------------------------------------------------------
# Patrones de validación (mismos que se usan en las ventanas con
# QRegularExpressionValidator)
# ---------------------------------------------------------------------------

RE_LETRAS = re.compile(r"^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s]+$")
RE_NUMEROS = re.compile(r"^[0-9]+$")
RE_PRECIO = re.compile(r"^[0-9]*\.?[0-9]*$")
RE_TITULO = re.compile(r"^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ0-9\s]+$")
RE_DIRECCION = re.compile(r"^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ0-9\s#\-.,]+$")
RE_VENCIMIENTO = re.compile(r"^\d{2}/\d{2}$")


# ---------------------------------------------------------------------------
# Funciones de validación extraídas de la lógica de negocio
# (sin dependencia de PySide6)
# ---------------------------------------------------------------------------

def validar_numero_tarjeta(numero: str) -> bool:
    """El número de tarjeta debe tener exactamente 16 dígitos."""
    limpio = numero.replace(" ", "").strip()
    return limpio.isdigit() and len(limpio) == 16


def validar_vencimiento(venc: str) -> tuple:
    """
    Valida el formato MM/AA y que el mes sea 1-12.
    Retorna (True, mm, aa) si es válido, o (False, None, None) en caso contrario.
    """
    if not re.fullmatch(r"\d{2}/\d{2}", venc.strip()):
        return False, None, None
    mm = int(venc[:2])
    aa = int(venc[3:])
    if mm < 1 or mm > 12:
        return False, None, None
    return True, mm, aa


def validar_cvv(cvv: str) -> bool:
    """El CVV debe tener exactamente 3 dígitos."""
    return cvv.strip().isdigit() and len(cvv.strip()) == 3


def validar_fechas_exhibicion(fecha_inicio: date, fecha_fin: date) -> bool:
    """La fecha fin no puede ser anterior a la fecha inicio."""
    return fecha_fin >= fecha_inicio


def validar_horas_misma_fecha(hora_inicio: tuple, hora_fin: tuple) -> bool:
    """
    Si la fecha es la misma, la hora fin no puede ser menor que la hora inicio.
    hora_inicio y hora_fin son tuplas (hora, minuto).
    """
    return hora_fin >= hora_inicio


# ===========================================================================
# PRUEBAS: Nombres (solo letras y espacios)
# ===========================================================================

class TestValidadorNombres(unittest.TestCase):
    """Nombres de personas: solo letras (incluyendo acentos) y espacios."""

    def test_nombre_valido_simple(self):
        self.assertTrue(RE_LETRAS.match("Juan"))

    def test_nombre_valido_con_espacio(self):
        self.assertTrue(RE_LETRAS.match("María José"))

    def test_nombre_valido_acentos(self):
        self.assertTrue(RE_LETRAS.match("Andrés Martínez"))

    def test_nombre_valido_enye(self):
        self.assertTrue(RE_LETRAS.match("Año Nuevo"))

    def test_nombre_valido_mayusculas(self):
        self.assertTrue(RE_LETRAS.match("GARCIA LOPEZ"))

    def test_nombre_con_numero_invalido(self):
        """Un nombre NO puede contener dígitos."""
        self.assertIsNone(RE_LETRAS.match("Juan123"))

    def test_nombre_solo_numeros_invalido(self):
        """Un campo de nombre NO puede ser solo números."""
        self.assertIsNone(RE_LETRAS.match("12345"))

    def test_nombre_con_simbolo_invalido(self):
        """Un nombre NO puede contener símbolos especiales."""
        self.assertIsNone(RE_LETRAS.match("Juan@García"))

    def test_nombre_con_guion_invalido(self):
        """Un guion no está permitido en nombres de personas."""
        self.assertIsNone(RE_LETRAS.match("García-López"))

    def test_nombre_vacio_invalido(self):
        """Un nombre vacío no es válido (no cumple el patrón +)."""
        self.assertIsNone(RE_LETRAS.match(""))


# ===========================================================================
# PRUEBAS: Campos numéricos (teléfono, ID)
# ===========================================================================

class TestValidadorNumeros(unittest.TestCase):
    """Campos numéricos: solo dígitos, sin letras ni símbolos."""

    def test_telefono_valido(self):
        self.assertTrue(RE_NUMEROS.match("5512345678"))

    def test_id_valido(self):
        self.assertTrue(RE_NUMEROS.match("42"))

    def test_numero_con_letra_invalido(self):
        """Un teléfono NO puede contener letras."""
        self.assertIsNone(RE_NUMEROS.match("551abc678"))

    def test_solo_letras_invalido(self):
        """Un campo numérico NO puede ser letras."""
        self.assertIsNone(RE_NUMEROS.match("abc"))

    def test_numero_con_guion_invalido(self):
        """Un guion no está permitido en campos numéricos puros."""
        self.assertIsNone(RE_NUMEROS.match("55-1234-5678"))

    def test_numero_con_punto_invalido(self):
        """Un punto no está permitido en campos de solo enteros."""
        self.assertIsNone(RE_NUMEROS.match("123.45"))

    def test_numero_vacio_invalido(self):
        self.assertIsNone(RE_NUMEROS.match(""))


# ===========================================================================
# PRUEBAS: Precio (decimal)
# ===========================================================================

class TestValidadorPrecio(unittest.TestCase):
    """Precio: número decimal no negativo (sin letras)."""

    def test_precio_entero_valido(self):
        self.assertTrue(RE_PRECIO.match("1000"))

    def test_precio_decimal_valido(self):
        self.assertTrue(RE_PRECIO.match("99.99"))

    def test_precio_cero_valido(self):
        self.assertTrue(RE_PRECIO.match("0"))

    def test_precio_fraccion_valido(self):
        self.assertTrue(RE_PRECIO.match("0.5"))

    def test_precio_con_letras_invalido(self):
        """Un precio NO puede contener letras."""
        self.assertIsNone(RE_PRECIO.match("abc"))

    def test_precio_con_letras_mezclado_invalido(self):
        """Un precio NO puede mezclar letras y números."""
        self.assertIsNone(RE_PRECIO.match("100abc"))

    def test_precio_doble_punto_invalido(self):
        """Un precio NO puede tener dos puntos decimales."""
        self.assertIsNone(RE_PRECIO.match("99.99.00"))

    def test_precio_con_coma_invalido(self):
        """Se usa punto como separador decimal, no coma."""
        self.assertIsNone(RE_PRECIO.match("1,000"))

    def test_precio_negativo_invalido(self):
        """Precios negativos no están permitidos."""
        self.assertIsNone(RE_PRECIO.match("-50"))


# ===========================================================================
# PRUEBAS: Título de pinturas (alfanumérico + espacios)
# ===========================================================================

class TestValidadorTitulo(unittest.TestCase):
    """Títulos de pinturas: letras, números y espacios permitidos."""

    def test_titulo_solo_letras_valido(self):
        self.assertTrue(RE_TITULO.match("La Gioconda"))

    def test_titulo_con_numero_valido(self):
        """Los títulos de pinturas pueden incluir números."""
        self.assertTrue(RE_TITULO.match("Serie 2024"))

    def test_titulo_con_acento_valido(self):
        self.assertTrue(RE_TITULO.match("Árboles en Otoño"))

    def test_titulo_con_simbolo_invalido(self):
        """Un título NO puede contener símbolos como '!'."""
        self.assertIsNone(RE_TITULO.match("Título #1"))

    def test_titulo_con_guion_invalido(self):
        """Un guion no está permitido en títulos."""
        self.assertIsNone(RE_TITULO.match("Sol-Luna"))

    def test_titulo_vacio_invalido(self):
        self.assertIsNone(RE_TITULO.match(""))


# ===========================================================================
# PRUEBAS: Dirección de proveedores
# ===========================================================================

class TestValidadorDireccion(unittest.TestCase):
    """Dirección: letras, números, espacios y #-., permitidos."""

    def test_direccion_valida_completa(self):
        self.assertTrue(RE_DIRECCION.match("Av. Principal #42, Col. Centro"))

    def test_direccion_simple_valida(self):
        self.assertTrue(RE_DIRECCION.match("Calle 5 Norte"))

    def test_direccion_con_guion_valida(self):
        self.assertTrue(RE_DIRECCION.match("Blvd. Norte-Sur 100"))

    def test_direccion_con_arroba_invalida(self):
        """Una dirección NO puede contener '@'."""
        self.assertIsNone(RE_DIRECCION.match("Calle@123"))

    def test_direccion_con_exclamacion_invalida(self):
        """Una dirección NO puede contener '!'."""
        self.assertIsNone(RE_DIRECCION.match("Calle Principal!"))

    def test_direccion_vacia_invalida(self):
        self.assertIsNone(RE_DIRECCION.match(""))


# ===========================================================================
# PRUEBAS: Validación de tarjeta (lógica de RealizarVenta)
# ===========================================================================

class TestValidacionTarjeta(unittest.TestCase):
    """Validación del número de tarjeta, fecha de vencimiento y CVV."""

    # --- Número de tarjeta ---

    def test_numero_tarjeta_valido(self):
        self.assertTrue(validar_numero_tarjeta("1234567890123456"))

    def test_numero_tarjeta_con_espacios_valido(self):
        """Los espacios en la UI se eliminan antes de validar."""
        self.assertTrue(validar_numero_tarjeta("1234 5678 9012 3456"))

    def test_numero_tarjeta_corto_invalido(self):
        """Menos de 16 dígitos debe rechazarse."""
        self.assertFalse(validar_numero_tarjeta("12345678"))

    def test_numero_tarjeta_largo_invalido(self):
        """Más de 16 dígitos debe rechazarse."""
        self.assertFalse(validar_numero_tarjeta("12345678901234567"))

    def test_numero_tarjeta_con_letras_invalido(self):
        self.assertFalse(validar_numero_tarjeta("1234abcd90123456"))

    # --- Fecha de vencimiento ---

    def test_vencimiento_valido(self):
        ok, mm, aa = validar_vencimiento("12/30")
        self.assertTrue(ok)
        self.assertEqual(mm, 12)
        self.assertEqual(aa, 30)

    def test_vencimiento_mes_minimo_valido(self):
        ok, mm, _ = validar_vencimiento("01/28")
        self.assertTrue(ok)
        self.assertEqual(mm, 1)

    def test_vencimiento_formato_invalido_letras(self):
        """La fecha NO puede tener letras."""
        ok, _, _ = validar_vencimiento("AB/CD")
        self.assertFalse(ok)

    def test_vencimiento_formato_sin_barra_invalido(self):
        ok, _, _ = validar_vencimiento("1230")
        self.assertFalse(ok)

    def test_vencimiento_mes_cero_invalido(self):
        ok, _, _ = validar_vencimiento("00/30")
        self.assertFalse(ok)

    def test_vencimiento_mes_13_invalido(self):
        ok, _, _ = validar_vencimiento("13/30")
        self.assertFalse(ok)

    # --- CVV ---

    def test_cvv_valido(self):
        self.assertTrue(validar_cvv("123"))

    def test_cvv_corto_invalido(self):
        """CVV de menos de 3 dígitos es inválido."""
        self.assertFalse(validar_cvv("12"))

    def test_cvv_largo_invalido(self):
        """CVV de más de 3 dígitos es inválido."""
        self.assertFalse(validar_cvv("1234"))

    def test_cvv_con_letras_invalido(self):
        self.assertFalse(validar_cvv("12a"))

    def test_cvv_vacio_invalido(self):
        self.assertFalse(validar_cvv(""))


# ===========================================================================
# PRUEBAS: Validación de fechas en Exhibiciones
# ===========================================================================

class TestValidacionFechasExhibicion(unittest.TestCase):
    """La fecha fin no puede ser anterior a la fecha inicio."""

    def test_fecha_fin_mayor_valida(self):
        inicio = date(2025, 1, 1)
        fin = date(2025, 1, 31)
        self.assertTrue(validar_fechas_exhibicion(inicio, fin))

    def test_fechas_iguales_validas(self):
        d = date(2025, 6, 15)
        self.assertTrue(validar_fechas_exhibicion(d, d))

    def test_fecha_fin_anterior_invalida(self):
        inicio = date(2025, 5, 10)
        fin = date(2025, 5, 5)
        self.assertFalse(validar_fechas_exhibicion(inicio, fin))

    def test_fecha_fin_ano_anterior_invalida(self):
        inicio = date(2025, 3, 1)
        fin = date(2024, 12, 31)
        self.assertFalse(validar_fechas_exhibicion(inicio, fin))


class TestValidacionHorasExhibicion(unittest.TestCase):
    """Si la fecha es la misma, la hora fin no puede ser menor que la hora inicio."""

    def test_hora_fin_mayor_valida(self):
        self.assertTrue(validar_horas_misma_fecha((10, 0), (18, 0)))

    def test_horas_iguales_validas(self):
        self.assertTrue(validar_horas_misma_fecha((9, 30), (9, 30)))

    def test_hora_fin_menor_invalida(self):
        self.assertFalse(validar_horas_misma_fecha((15, 0), (10, 0)))

    def test_hora_fin_minuto_menor_invalido(self):
        self.assertFalse(validar_horas_misma_fecha((9, 45), (9, 30)))


if __name__ == "__main__":
    unittest.main()

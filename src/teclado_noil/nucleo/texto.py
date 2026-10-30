"""Logica pura del texto que Noil escribe. Sin pygame, sin archivos."""
from __future__ import annotations

import unicodedata

LETRAS_VALIDAS = frozenset("ABCDEFGHIJKLMNOPQRSTUVWXYZÑ")
DIGITOS_VALIDOS = frozenset("0123456789")
# Hasta aqui crece la linea del centro antes de empezar a desplazarse.
MAXIMO_VISIBLE = 14


def normalizar(texto: str) -> str:
    """Pasa a mayusculas y quita acentos y dieresis, conservando la enie.

    'pingüino' -> 'PINGUINO', 'mamá' -> 'MAMA', 'niño' -> 'NIÑO'.
    Asi lo que Noil puede teclear coincide con el diccionario.
    """
    descompuesto = unicodedata.normalize("NFD", texto)
    sin_acentos = "".join(
        c for c in descompuesto
        if unicodedata.category(c) != "Mn" or c == "̃"
    )
    return unicodedata.normalize("NFC", sin_acentos).upper()


class EstadoTexto:
    """Lo escrito en el centro de la pantalla y las palabras ya descubiertas.

    Las palabras se separan con espacio o con un digito: un numero corta la
    palabra en curso igual que un espacio.
    """

    def __init__(self) -> None:
        self.contenido: str = ""
        self.descubiertas: list[str] = []

    @property
    def palabra_actual(self) -> str:
        """Tramo final formado solo por letras."""
        letras: list[str] = []
        for caracter in reversed(self.contenido):
            if caracter in LETRAS_VALIDAS:
                letras.append(caracter)
            else:
                break
        return "".join(reversed(letras))

    @property
    def visible(self) -> str:
        """Cola del contenido que cabe en pantalla."""
        return self.contenido[-MAXIMO_VISIBLE:]

    def escribir(self, caracter: str) -> None:
        """Agrega una letra, un digito o un espacio ya validados."""
        self.contenido += caracter

    def retroceso(self) -> bool:
        """Borra el ultimo caracter. Devuelve si hubo algo que borrar."""
        if not self.contenido:
            return False
        self.contenido = self.contenido[:-1]
        return True

    def limpiar(self) -> bool:
        """Vacia el centro; el historial de descubiertas se conserva."""
        if not self.contenido:
            return False
        self.contenido = ""
        return True

    def registrar_descubierta(self, palabra: str) -> None:
        """Guarda una palabra acertada, sin repetirla en el historial."""
        if palabra not in self.descubiertas:
            self.descubiertas.append(palabra)

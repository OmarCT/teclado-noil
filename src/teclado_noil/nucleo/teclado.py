"""Clasificacion de pulsaciones. Logica pura: no sabe de pygame."""
from __future__ import annotations

from enum import Enum, auto

from .texto import DIGITOS_VALIDOS, LETRAS_VALIDAS, normalizar


class Tipo(Enum):
    LETRA = auto()
    DIGITO = auto()
    ESPACIO = auto()
    IGNORADA = auto()


class Pulsacion:
    __slots__ = ("tipo", "caracter")

    def __init__(self, tipo: Tipo, caracter: str = "") -> None:
        self.tipo = tipo
        self.caracter = caracter

    def __eq__(self, otro: object) -> bool:
        return (
            isinstance(otro, Pulsacion)
            and otro.tipo is self.tipo
            and otro.caracter == self.caracter
        )

    def __repr__(self) -> str:
        return f"Pulsacion({self.tipo.name}, {self.caracter!r})"


IGNORADA = Pulsacion(Tipo.IGNORADA)


def clasificar(caracter: str, aceptar_digitos: bool = True) -> Pulsacion:
    """Traduce el caracter de una tecla a lo que la app debe hacer.

    Las letras suben a mayuscula se haya usado Shift o no: Noil ve siempre la
    misma forma, la de los libros y la de las teclas del teclado.
    """
    if not caracter:
        return IGNORADA
    if caracter == " ":
        return Pulsacion(Tipo.ESPACIO, " ")
    if len(caracter) != 1:
        return IGNORADA
    if caracter in DIGITOS_VALIDOS:
        return Pulsacion(Tipo.DIGITO, caracter) if aceptar_digitos else IGNORADA
    letra = normalizar(caracter)
    if letra in LETRAS_VALIDAS:
        return Pulsacion(Tipo.LETRA, letra)
    return IGNORADA

"""Nombres de los archivos de audio. Compartidos por la app y el generador."""
from __future__ import annotations


def archivo_letra(simbolo: str, parte: str) -> str:
    """parte es 'nombre' ("eme") o 'sonido' ("mmm")."""
    return f"letra_{simbolo}_{parte}.wav"


def archivo_digito(digito: str) -> str:
    return f"digito_{digito}.wav"


def archivo_palabra(texto: str) -> str:
    return f"palabra_{texto}.wav"


ARCHIVO_RETROCESO = "efecto_retroceso.wav"

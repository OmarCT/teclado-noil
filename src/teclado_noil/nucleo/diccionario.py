"""Carga del vocabulario y busqueda de palabras acertadas."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from .texto import normalizar


@dataclass(frozen=True)
class Palabra:
    texto: str
    nivel: int = 1
    pronunciacion: str | None = None
    nombre_propio: bool = False
    traduccion: str | None = None

    @property
    def para_decir(self) -> str:
        """Lo que el TTS debe leer: la grafia con acentos si la hay."""
        return self.pronunciacion or self.texto.lower()


@dataclass(frozen=True)
class Letra:
    simbolo: str
    nombre: str
    sonido: str


@dataclass
class Idioma:
    codigo: str
    etiqueta: str
    voz_tts: str
    longitud_minima: int
    letras: dict[str, Letra] = field(default_factory=dict)
    digitos: dict[str, str] = field(default_factory=dict)
    palabras: list[Palabra] = field(default_factory=list)


def cargar_idioma(ruta: Path) -> Idioma:
    datos = json.loads(ruta.read_text(encoding="utf-8"))
    return Idioma(
        codigo=datos["idioma"],
        etiqueta=datos["etiqueta"],
        voz_tts=datos["voz_tts"],
        longitud_minima=datos.get("longitud_minima", 3),
        letras={
            simbolo: Letra(simbolo, valor["nombre"], valor["sonido"])
            for simbolo, valor in datos["letras"].items()
        },
        digitos={d: valor["nombre"] for d, valor in datos["digitos"].items()},
        palabras=[
            Palabra(
                texto=p["texto"],
                nivel=p.get("nivel", 1),
                pronunciacion=p.get("pronunciacion"),
                nombre_propio=p.get("nombre_propio", False),
                traduccion=p.get("traduccion"),
            )
            for p in datos["palabras"]
        ],
    )


class Diccionario:
    """Busca coincidencias exactas, filtrando por el nivel activo."""

    def __init__(self, idioma: Idioma, nivel_maximo: int = 1) -> None:
        self.idioma = idioma
        self.nivel_maximo = nivel_maximo
        self._por_texto = {
            p.texto: p for p in idioma.palabras if p.nivel <= nivel_maximo
        }

    def __len__(self) -> int:
        return len(self._por_texto)

    def buscar(self, palabra: str) -> Palabra | None:
        """Devuelve la palabra si lo tecleado la forma exactamente."""
        clave = normalizar(palabra)
        if len(clave) < self.idioma.longitud_minima:
            return None
        return self._por_texto.get(clave)

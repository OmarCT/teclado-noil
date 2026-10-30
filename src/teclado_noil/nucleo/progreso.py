"""Progreso entre sesiones: las palabras que Noil ya descubrio.

Un JSON pequeno, no una base de datos: la app es un juguete, no un sistema.
Si el archivo esta corrupto o no se puede escribir, el juego sigue igual.
"""
from __future__ import annotations

import json
from pathlib import Path


def cargar(ruta: Path) -> list[str]:
    if not ruta.is_file():
        return []
    try:
        datos = json.loads(ruta.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    descubiertas = datos.get("descubiertas", [])
    return [p for p in descubiertas if isinstance(p, str)]


def guardar(ruta: Path, descubiertas: list[str]) -> None:
    contenido = {"descubiertas": descubiertas}
    try:
        ruta.write_text(
            json.dumps(contenido, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    except OSError:
        pass  # nunca interrumpir el juego por no poder guardar

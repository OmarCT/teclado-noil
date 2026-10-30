"""Rutas y ajustes del juego.

Todo lo que un adulto podria querer cambiar sin tocar logica vive aqui.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path


def ruta_base() -> Path:
    """Raiz de los recursos, tanto en desarrollo como dentro del .exe."""
    empaquetado = getattr(sys, "_MEIPASS", None)
    if empaquetado:
        return Path(empaquetado)
    return Path(__file__).resolve().parents[2]


RAIZ = ruta_base()
DIR_DATOS = RAIZ / "datos"
DIR_AUDIO = RAIZ / "assets" / "audio"
DIR_FUENTES = RAIZ / "assets" / "fuentes"


def ruta_progreso() -> Path:
    """Archivo de progreso: junto al ejecutable, nunca dentro del paquete."""
    if getattr(sys, "_MEIPASS", None):
        return Path(sys.executable).parent / "progreso.json"
    return RAIZ / "progreso.json"


@dataclass
class Ajustes:
    idioma: str = "es"
    # Nivel maximo de vocabulario activo: 1 = palabras que Noil ya conoce,
    # 2 = vocabulario de 3 a 5 anos. Subelo cuando crezca.
    nivel_maximo: int = 1
    # "ambos" dice "eme... mmm"; tambien vale "nombre" o "sonido".
    modo_letra: str = "ambos"
    pantalla_completa: bool = True
    # Solo se usa cuando pantalla_completa es False (desarrollo).
    tamano_ventana: tuple[int, int] = (1280, 720)
    fps: int = 60
    # Segundos quieto antes de que las letras empiecen a "respirar".
    segundos_inactividad: float = 30.0
    # Segundos que hay que mantener Ctrl+Shift+Q para salir.
    segundos_salida: float = 2.0
    mostrar_digitos: bool = True
    guardar_progreso: bool = True


AJUSTES = Ajustes()

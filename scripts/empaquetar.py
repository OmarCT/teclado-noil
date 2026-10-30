"""Construye el ejecutable con PyInstaller (ejecutar en Windows para el .exe).

    python scripts/empaquetar.py             un solo archivo .exe
    python scripts/empaquetar.py --carpeta   una carpeta que arranca al instante

Un solo archivo es comodo de copiar, pero cada arranque descomprime los 50 MB
de voz en una carpeta temporal y tarda unos segundos. La version en carpeta
arranca de inmediato: para dejarsela a Noil en el escritorio, un acceso directo
al .exe de dentro.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
NOMBRE = "Teclado de Noil"


def main() -> int:
    analizador = argparse.ArgumentParser(description=__doc__)
    analizador.add_argument(
        "--carpeta",
        action="store_true",
        help="generar una carpeta en vez de un archivo unico (arranca al instante)",
    )
    args = analizador.parse_args()

    separador = ";" if sys.platform == "win32" else ":"
    comando = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm", "--clean",
        "--onedir" if args.carpeta else "--onefile",
        "--windowed",
        "--name", NOMBRE,
        # Sin esto, PyInstaller no encuentra el paquete: main.py agrega src/ al
        # sys.path en tiempo de ejecucion, y el analisis de imports es estatico.
        "--paths", str(RAIZ / "src"),
        "--hidden-import", "teclado_noil.app",
        "--add-data", f"{RAIZ / 'datos'}{separador}datos",
        "--add-data", f"{RAIZ / 'assets'}{separador}assets",
        str(RAIZ / "main.py"),
    ]
    print(" ".join(comando))
    codigo = subprocess.call(comando, cwd=RAIZ)
    if codigo == 0:
        destino = RAIZ / "dist" / (NOMBRE if args.carpeta else NOMBRE)
        print(f"\nListo: {destino}")
    return codigo


if __name__ == "__main__":
    sys.exit(main())

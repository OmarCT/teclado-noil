"""Punto de entrada: .venv/bin/python main.py"""
import sys
from pathlib import Path

RAIZ = Path(__file__).parent
# En desarrollo el paquete vive en src/. Dentro del ejecutable ya viene
# empaquetado, y esa carpeta no existe.
FUENTES = RAIZ / "src"
if FUENTES.is_dir():
    sys.path.insert(0, str(FUENTES))

try:
    from teclado_noil.app import main
except ModuleNotFoundError as falta:
    if falta.name != "pygame":
        raise
    # El fallo tipico: ejecutar con el Python del sistema en vez del del proyecto.
    print(
        "Falta pygame, asi que seguramente estas usando otro Python.\n\n"
        "  Prueba:   .venv/bin/python main.py\n"
        "  O activa el entorno:   source .venv/bin/activate\n\n"
        "  Y si todavia no existe el entorno:\n"
        "    uv venv && uv pip install -e \".[dev]\"\n",
        file=sys.stderr,
    )
    raise SystemExit(1) from None

if __name__ == "__main__":
    main()

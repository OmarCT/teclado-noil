"""Busca clips que el sintetizador probablemente leyo mal.

Cuando edge-tts no reconoce una grafia, la deletrea: "Nóil" sonaba "ene-oil" y
"mmm" sonaba "triple eme". Deletrear tarda mucho mas que pronunciar, asi que
un clip anormalmente largo para lo que dice delata el problema sin tener que
escuchar los 771 uno por uno.

    python scripts/revisar_audio.py
    python scripts/revisar_audio.py --tolerancia 1.8

Lo que salga en la lista hay que escucharlo; si suena deletreado, se corrige
el campo `pronunciacion` de esa palabra en datos/<idioma>.json y se regenera
con `generar_audio.py --forzar --solo palabras`.

Comparar duracion por letra no sirve: hablar tiene un costo fijo de arranque,
asi que los textos de una o dos letras siempre parecerian lentos. Lo que se
compara es cada clip contra lo que deberia durar un texto de ese largo, segun
una recta ajustada a todos los demas.
"""
from __future__ import annotations

import argparse
import os
import statistics
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

from teclado_noil import audio  # noqa: E402
from teclado_noil.audio import nombres  # noqa: E402
from teclado_noil.nucleo.diccionario import cargar_idioma  # noqa: E402


def main() -> int:
    analizador = argparse.ArgumentParser(description=__doc__)
    analizador.add_argument("--idioma", default="es")
    analizador.add_argument(
        "--tolerancia",
        type=float,
        default=1.6,
        help="cuantas veces la duracion normal por letra ya es sospechosa",
    )
    args = analizador.parse_args()

    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    import pygame

    pygame.mixer.init(audio.FRECUENCIA, -16, audio.CANALES, 1024)

    idioma = cargar_idioma(RAIZ / "datos" / f"{args.idioma}.json")
    directorio = RAIZ / "assets" / "audio" / args.idioma

    medidos: list[tuple[int, float, str, str]] = []
    faltan: list[str] = []
    por_revisar = [(p.texto, p.para_decir, nombres.archivo_palabra(p.texto))
                   for p in idioma.palabras]
    por_revisar += [
        (f"letra {simbolo}", letra.nombre, nombres.archivo_letra(simbolo, "nombre"))
        for simbolo, letra in idioma.letras.items()
    ]
    por_revisar += [
        (f"sonido {simbolo}", letra.sonido, nombres.archivo_letra(simbolo, "sonido"))
        for simbolo, letra in idioma.letras.items()
        if letra.sonido
    ]
    por_revisar += [
        (f"digito {d}", nombre, nombres.archivo_digito(d))
        for d, nombre in idioma.digitos.items()
    ]

    for etiqueta, dicho, archivo in por_revisar:
        ruta = directorio / archivo
        if not ruta.is_file():
            faltan.append(archivo)
            continue
        duracion = pygame.mixer.Sound(str(ruta)).get_length()
        letras = max(1, len(dicho.replace(" ", "")))
        medidos.append((letras, duracion, etiqueta, dicho))

    if not medidos:
        print("No hay clips que revisar. Corre primero generar_audio.py")
        return 1

    arranque, por_letra = _ajustar_recta(medidos)
    print(f"clips revisados: {len(medidos)}")
    print(
        f"duracion normal: {arranque:.2f}s de arranque + {por_letra:.3f}s por letra"
        f"   (sospechoso: {args.tolerancia:g} veces eso)"
    )
    if faltan:
        print(f"faltan {len(faltan)} clips por generar, por ejemplo {faltan[:3]}")

    sospechosos = []
    for letras, duracion, etiqueta, dicho in medidos:
        esperado = arranque + por_letra * letras
        if duracion > esperado * args.tolerancia:
            sospechosos.append((duracion / esperado, duracion, esperado, etiqueta, dicho))

    if not sospechosos:
        print("\nNinguno parece deletreado.")
        return 0
    print(f"\n{len(sospechosos)} para escuchar:")
    for veces, duracion, esperado, etiqueta, dicho in sorted(sospechosos, reverse=True):
        print(
            f'  {etiqueta:16} se le pide "{dicho}"  {duracion:.2f}s '
            f"cuando deberia durar {esperado:.2f}s  ({veces:.1f} veces mas)"
        )
    return 0


def _ajustar_recta(medidos) -> tuple[float, float]:
    """Minimos cuadrados: cuanto dura hablar, segun cuantas letras se dicen."""
    n = len(medidos)
    suma_x = sum(letras for letras, _, _, _ in medidos)
    suma_y = sum(duracion for _, duracion, _, _ in medidos)
    suma_xy = sum(letras * duracion for letras, duracion, _, _ in medidos)
    suma_xx = sum(letras * letras for letras, _, _, _ in medidos)
    denominador = n * suma_xx - suma_x * suma_x
    if not denominador:
        return 0.0, statistics.median(d for _, d, _, _ in medidos)
    pendiente = (n * suma_xy - suma_x * suma_y) / denominador
    arranque = (suma_y - pendiente * suma_x) / n
    return arranque, pendiente


if __name__ == "__main__":
    sys.exit(main())

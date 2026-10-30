"""Genera los clips de voz con edge-tts y los guarda en assets/audio/<idioma>.

Se ejecuta una sola vez (y de nuevo cuando agregues palabras): solo crea lo que
falta. Los clips se versionan en el repo para que el .exe funcione sin internet.

    python scripts/generar_audio.py              # lo que falte del espanol
    python scripts/generar_audio.py --forzar     # regenerar todo
    python scripts/generar_audio.py --solo letras

Para reemplazar cualquier clip por una grabacion real, basta sobrescribir el
archivo: la app no distingue de donde salio.
"""
from __future__ import annotations

import argparse
import array
import asyncio
import math
import os
import struct
import sys
import tempfile
import wave
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

from teclado_noil import audio  # noqa: E402
from teclado_noil.audio import nombres  # noqa: E402
from teclado_noil.nucleo.diccionario import cargar_idioma  # noqa: E402

# Un poco mas lento que el habla normal: a los 3 anos se entiende mejor.
RITMO_LETRA = "-15%"
RITMO_PALABRA = "-10%"
PETICIONES_EN_PARALELO = 6
# edge-tts devuelve casi dos segundos de silencio alrededor de cada palabra.
# Con un nino que teclea cada pocas decimas, ese silencio es la diferencia
# entre oir la letra y no oir nada: hay que recortarlo.
UMBRAL_SILENCIO = 0.02   # fraccion del pico que ya cuenta como sonido
MARGEN_INICIAL = 0.02    # segundos que se dejan antes del primer sonido
MARGEN_FINAL = 0.06      # y despues del ultimo


def tareas_de_voz(idioma, solo: str) -> list[tuple[str, str, str]]:
    """Lista de (archivo, texto a leer, ritmo)."""
    tareas: list[tuple[str, str, str]] = []
    if solo in ("todo", "letras"):
        for simbolo, letra in idioma.letras.items():
            tareas.append(
                (nombres.archivo_letra(simbolo, "nombre"), letra.nombre, RITMO_LETRA)
            )
            # Sonido vacio: las vocales ya suenan como se llaman, y para H, W
            # y X no hay silaba natural en espanol. Solo se dice el nombre.
            if letra.sonido:
                tareas.append(
                    (nombres.archivo_letra(simbolo, "sonido"), letra.sonido, RITMO_LETRA)
                )
    if solo in ("todo", "digitos"):
        for digito, nombre in idioma.digitos.items():
            tareas.append((nombres.archivo_digito(digito), nombre, RITMO_LETRA))
    if solo in ("todo", "palabras"):
        for palabra in idioma.palabras:
            tareas.append(
                (nombres.archivo_palabra(palabra.texto), palabra.para_decir, RITMO_PALABRA)
            )
    return tareas


def generar_efecto_retroceso(ruta: Path) -> None:
    """Tono descendente suave para el borrado. Sin dependencias ni TTS."""
    frecuencia_muestreo = audio.FRECUENCIA
    duracion = 0.18
    total = int(frecuencia_muestreo * duracion)
    cuadros = bytearray()
    for i in range(total):
        t = i / frecuencia_muestreo
        avance = i / total
        frecuencia = 560.0 - 260.0 * avance
        envolvente = math.sin(math.pi * avance) ** 1.5  # entra y sale sin clic
        muestra = int(16000 * envolvente * math.sin(2 * math.pi * frecuencia * t))
        cuadros += struct.pack("<h", muestra)
    with wave.open(str(ruta), "wb") as salida:
        salida.setnchannels(audio.CANALES)
        salida.setsampwidth(audio.ANCHO_MUESTRA)
        salida.setframerate(frecuencia_muestreo)
        salida.writeframes(bytes(cuadros))


def _recortar_silencio(muestras: array.array) -> array.array:
    """Quita el silencio de los extremos conservando un margen pequeno."""
    pico = max((abs(m) for m in muestras), default=0)
    if pico == 0:
        return muestras
    umbral = max(150, int(pico * UMBRAL_SILENCIO))
    inicio = 0
    fin = len(muestras) - 1
    while inicio < fin and abs(muestras[inicio]) < umbral:
        inicio += 1
    while fin > inicio and abs(muestras[fin]) < umbral:
        fin -= 1
    inicio = max(0, inicio - int(audio.FRECUENCIA * MARGEN_INICIAL))
    fin = min(len(muestras) - 1, fin + int(audio.FRECUENCIA * MARGEN_FINAL))
    return muestras[inicio : fin + 1]


def _mp3_a_wav_recortado(pygame, origen: Path, destino: Path) -> None:
    """Decodifica con pygame, recorta el silencio y guarda un wav ligero."""
    sonido = pygame.mixer.Sound(str(origen))
    muestras = array.array("h")
    muestras.frombytes(sonido.get_raw())
    recortadas = _recortar_silencio(muestras)
    with wave.open(str(destino), "wb") as salida:
        salida.setnchannels(audio.CANALES)
        salida.setsampwidth(audio.ANCHO_MUESTRA)
        salida.setframerate(audio.FRECUENCIA)
        salida.writeframes(recortadas.tobytes())


async def sintetizar(
    edge_tts, voz: str, texto: str, destino: Path, ritmo: str, limite: asyncio.Semaphore
) -> tuple[Path, Path | None, str | None]:
    """Pide el audio al servicio y lo deja en un mp3 temporal."""
    async with limite:
        temporal = Path(tempfile.gettempdir()) / f"tn_{os.getpid()}_{destino.stem}.mp3"
        try:
            comunicacion = edge_tts.Communicate(texto, voz, rate=ritmo)
            await comunicacion.save(str(temporal))
            return destino, temporal, None
        except Exception as error:  # red caida, voz inexistente, limite del servicio
            temporal.unlink(missing_ok=True)
            return destino, None, f"{type(error).__name__}: {error}"


async def principal(args) -> int:
    try:
        import edge_tts
    except ImportError:
        print("Falta edge-tts. Instalalo con:  uv pip install edge-tts")
        return 1

    # El mixer se abre ya en el formato final: al cargar el mp3, pygame lo
    # convierte a 22 kHz mono y get_raw() devuelve justo lo que hay que grabar.
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    import pygame

    pygame.mixer.init(audio.FRECUENCIA, -16, audio.CANALES, 1024)

    idioma = cargar_idioma(RAIZ / "datos" / f"{args.idioma}.json")
    directorio = RAIZ / "assets" / "audio" / args.idioma
    directorio.mkdir(parents=True, exist_ok=True)

    if args.solo in ("todo", "efectos"):
        ruta_efecto = directorio / nombres.ARCHIVO_RETROCESO
        if args.forzar or not ruta_efecto.is_file():
            generar_efecto_retroceso(ruta_efecto)
            print(f"efecto de retroceso -> {ruta_efecto.name}")

    tareas = tareas_de_voz(idioma, args.solo)
    pendientes = [
        (archivo, texto, ritmo)
        for archivo, texto, ritmo in tareas
        if args.forzar or not (directorio / archivo).is_file()
    ]
    print(f"voz: {idioma.voz_tts}")
    print(f"clips totales: {len(tareas)}   por generar: {len(pendientes)}")
    if not pendientes:
        return 0

    limite = asyncio.Semaphore(PETICIONES_EN_PARALELO)
    trabajos = [
        sintetizar(edge_tts, idioma.voz_tts, texto, directorio / archivo, ritmo, limite)
        for archivo, texto, ritmo in pendientes
    ]
    fallos: list[str] = []
    for indice, completado in enumerate(asyncio.as_completed(trabajos), start=1):
        destino, temporal, error = await completado
        if error:
            fallos.append(f"{destino.name}: {error}")
        else:
            try:
                _mp3_a_wav_recortado(pygame, temporal, destino)
            except Exception as fallo:
                fallos.append(f"{destino.name}: al recortar: {fallo}")
                destino.unlink(missing_ok=True)
            finally:
                temporal.unlink(missing_ok=True)
        if indice % 25 == 0 or indice == len(trabajos):
            print(f"  {indice}/{len(trabajos)}")

    if fallos:
        print(f"\n{len(fallos)} fallaron (vuelve a ejecutar para reintentar):")
        for linea in fallos[:10]:
            print(f"  {linea}")
        return 1
    print("listo")
    return 0


if __name__ == "__main__":
    analizador = argparse.ArgumentParser(description=__doc__)
    analizador.add_argument("--idioma", default="es")
    analizador.add_argument("--forzar", action="store_true", help="regenerar lo que ya existe")
    analizador.add_argument(
        "--solo",
        default="todo",
        choices=["todo", "letras", "digitos", "palabras", "efectos"],
    )
    sys.exit(asyncio.run(principal(analizador.parse_args())))

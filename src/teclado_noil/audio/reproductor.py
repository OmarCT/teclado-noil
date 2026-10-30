"""Reproduccion de voz y efectos.

Toda la voz va por un unico canal, y nunca suenan dos voces a la vez: las
letras se interrumpen entre si para que la respuesta a cada tecla sea
inmediata, y la palabra acertada se encola detras del nombre de su ultima
letra, de modo que Noil oye "o... gato" y no las dos cosas encimadas.
"""
from __future__ import annotations

from pathlib import Path

import pygame

from ..nucleo.diccionario import Letra, Palabra
from . import nombres

CANAL_VOZ = 0
CANAL_EFECTOS = 1
VOLUMEN_VOZ = 0.9
VOLUMEN_PALABRA = 1.0
VOLUMEN_EFECTO = 0.35


class Reproductor:
    def __init__(self, directorio: Path, modo_letra: str = "ambos") -> None:
        self.directorio = directorio
        self.modo_letra = modo_letra
        self._cache: dict[str, pygame.mixer.Sound | None] = {}
        self._disponible = pygame.mixer.get_init() is not None
        if self._disponible:
            pygame.mixer.set_num_channels(4)
            self._canal_voz = pygame.mixer.Channel(CANAL_VOZ)
            self._canal_efectos = pygame.mixer.Channel(CANAL_EFECTOS)

    @property
    def disponible(self) -> bool:
        return self._disponible

    def _cargar(self, archivo: str) -> pygame.mixer.Sound | None:
        """Carga perezosa con cache: con 700 palabras no cabe todo en memoria.

        Si falta el archivo devuelve None y la app sigue en silencio, para que
        pueda ejecutarse antes de haber generado los audios.
        """
        if archivo in self._cache:
            return self._cache[archivo]
        ruta = self.directorio / archivo
        sonido: pygame.mixer.Sound | None = None
        if ruta.is_file():
            try:
                sonido = pygame.mixer.Sound(str(ruta))
            except pygame.error:
                sonido = None
        self._cache[archivo] = sonido
        return sonido

    def _partes_de_letra(self, letra: Letra, solo_nombre: bool = False) -> list:
        """Los clips de una letra: su nombre y, si toca, su sonido."""
        if solo_nombre:
            partes = ("nombre",)
        else:
            partes = {
                "ambos": ("nombre", "sonido"),
                "nombre": ("nombre",),
                "sonido": ("sonido",),
            }.get(self.modo_letra, ("nombre", "sonido"))
        return [
            sonido for parte in partes
            if (sonido := self._cargar(nombres.archivo_letra(letra.simbolo, parte)))
        ]

    def _decir(self, secuencia: list, volumenes: list[float]) -> None:
        """Reproduce el primer clip y encola el resto en el mismo canal.

        pygame solo admite un clip en cola, asi que la secuencia nunca pasa de
        dos: o el nombre y el sonido de la letra, o el nombre y la palabra.
        """
        if not secuencia:
            return
        for sonido, volumen in zip(secuencia, volumenes):
            sonido.set_volume(volumen)
        primero, *resto = secuencia
        self._canal_voz.play(primero)  # corta lo que estuviera sonando
        for siguiente in resto[:1]:
            self._canal_voz.queue(siguiente)

    def decir_letra(self, letra: Letra) -> None:
        """Dice "eme... ma": el nombre y despues la silaba."""
        if not self._disponible:
            return
        self._decir(self._partes_de_letra(letra), [VOLUMEN_VOZ, VOLUMEN_VOZ])

    def decir_letra_y_palabra(self, letra: Letra, palabra: Palabra) -> None:
        """Dice "o... gato": la letra que completo la palabra, y la palabra.

        Se omite la silaba de la letra: lo que importa ahora es la palabra, y
        tres clips seguidos no caben en la cola ni en la paciencia de un nino.
        """
        if not self._disponible:
            return
        secuencia = self._partes_de_letra(letra, solo_nombre=True)
        if sonido := self._cargar(nombres.archivo_palabra(palabra.texto)):
            secuencia.append(sonido)
        self._decir(secuencia, [VOLUMEN_VOZ, VOLUMEN_PALABRA])

    def decir_digito(self, digito: str) -> None:
        if not self._disponible:
            return
        if sonido := self._cargar(nombres.archivo_digito(digito)):
            self._decir([sonido], [VOLUMEN_VOZ])

    def decir_palabra(self, palabra: Palabra) -> None:
        if not self._disponible:
            return
        if sonido := self._cargar(nombres.archivo_palabra(palabra.texto)):
            self._decir([sonido], [VOLUMEN_PALABRA])

    def efecto_retroceso(self) -> None:
        """Va en su propio canal: es un ruidito, no una voz que estorbe."""
        if not self._disponible:
            return
        if sonido := self._cargar(nombres.ARCHIVO_RETROCESO):
            sonido.set_volume(VOLUMEN_EFECTO)
            self._canal_efectos.play(sonido)

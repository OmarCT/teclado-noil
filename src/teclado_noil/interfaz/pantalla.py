"""Dibujado de la pantalla: franja de palabras descubiertas y letra gigante."""
from __future__ import annotations

import math
from dataclasses import dataclass

import pygame

from .. import config, tema
from ..nucleo.texto import EstadoTexto
from .brillo import Celebracion, construir_halo

MARGEN_ANCHO = 0.86  # el texto deja aire a los lados para que quepa el resplandor
CENTRO_VERTICAL = 0.56
# Cuantas superficies ya dibujadas se guardan antes de empezar de cero.
LIMITE_CACHE = 48


def modo_video(ajustes: config.Ajustes) -> tuple[tuple[int, int], int]:
    """Tamano y banderas con los que abrir la ventana.

    En pantalla completa hay que pasar el tamano real del escritorio: SDL no
    acepta un modo de 0x0, y pygame no lo deduce solo en Windows.
    """
    if not ajustes.pantalla_completa:
        return ajustes.tamano_ventana, 0
    escritorios = pygame.display.get_desktop_sizes()
    if escritorios and all(escritorios[0]):
        return escritorios[0], pygame.FULLSCREEN
    return (0, 0), pygame.FULLSCREEN  # ultimo recurso: que lo resuelva SDL


@dataclass
class Metricas:
    """Donde va el texto y donde va la palabra que puede brillar."""

    fuente: pygame.font.Font
    texto: str
    rect_total: pygame.Rect
    rect_palabra: pygame.Rect | None


class Pantalla:
    def __init__(self, ajustes: config.Ajustes) -> None:
        self.ajustes = ajustes
        tamano, banderas = modo_video(ajustes)
        self.superficie = pygame.display.set_mode(tamano, banderas)
        pygame.display.set_caption("Teclado de Noil")
        pygame.mouse.set_visible(False)
        self.ancho, self.alto = self.superficie.get_size()
        self._ruta_fuente = config.DIR_FUENTES / tema.FUENTE_ARCHIVO
        self._fuentes: dict[int, pygame.font.Font] = {}
        # Dibujar texto y resplandor es caro a resolucion completa, y entre
        # fotograma y fotograma casi nunca cambian: se guardan ya dibujados.
        self._tamanos: dict[str, int] = {}
        self._textos: dict[tuple[str, int, tuple[int, int, int]], pygame.Surface] = {}
        self._halos: dict[tuple[str, int], pygame.Surface] = {}

    def _fuente(self, tamano: int) -> pygame.font.Font:
        """Cache por tamano: crear una Font en cada fotograma seria carisimo."""
        tamano = max(8, tamano)
        if tamano not in self._fuentes:
            if self._ruta_fuente.is_file():
                self._fuentes[tamano] = pygame.font.Font(str(self._ruta_fuente), tamano)
            else:
                self._fuentes[tamano] = pygame.font.Font(None, tamano)
        return self._fuentes[tamano]

    def _fuente_que_quepa(self, texto: str) -> pygame.font.Font:
        """Baja el tamano hasta que la linea entre en el ancho disponible."""
        if texto in self._tamanos:
            return self._fuente(self._tamanos[texto])
        maximo = int(self.alto * tema.ALTURA_LETRA)
        minimo = int(self.alto * tema.ALTURA_LETRA_MINIMA)
        disponible = int(self.ancho * MARGEN_ANCHO)
        tamano = maximo
        while tamano > minimo:
            if self._fuente(tamano).size(texto)[0] <= disponible:
                break
            tamano -= max(2, tamano // 24)
        self._guardar(self._tamanos, texto, tamano)
        return self._fuente(tamano)

    @staticmethod
    def _guardar(cache: dict, clave, valor):
        """Cache con tope: la app corre horas, no puede crecer sin limite."""
        if len(cache) >= LIMITE_CACHE:
            cache.clear()
        cache[clave] = valor
        return valor

    def _texto(
        self, fuente: pygame.font.Font, texto: str, color: tuple[int, int, int]
    ) -> pygame.Surface:
        clave = (texto, fuente.get_height(), color)
        dibujo = self._textos.get(clave)
        if dibujo is None:
            dibujo = self._guardar(
                self._textos, clave, fuente.render(texto, True, color)
            )
        return dibujo

    def _halo(self, fuente: pygame.font.Font, palabra: str) -> pygame.Surface:
        clave = (palabra, fuente.get_height())
        halo = self._halos.get(clave)
        if halo is None:
            halo = self._guardar(
                self._halos, clave, construir_halo(self._texto(fuente, palabra, tema.BRILLO))
            )
        return halo

    def metricas(self, estado: EstadoTexto) -> Metricas | None:
        """Mide el texto central. La app la usa para saber donde brillar."""
        visible = estado.visible
        if not visible:
            return None
        fuente = self._fuente_que_quepa(visible)
        ancho, alto = fuente.size(visible)
        rect_total = pygame.Rect(0, 0, ancho, alto)
        rect_total.center = (self.ancho // 2, int(self.alto * CENTRO_VERTICAL))

        rect_palabra = None
        palabra = estado.palabra_actual
        if palabra and visible.endswith(palabra):
            prefijo = visible[: len(visible) - len(palabra)]
            ancho_prefijo = fuente.size(prefijo)[0]
            ancho_palabra = fuente.size(palabra)[0]
            rect_palabra = pygame.Rect(
                rect_total.left + ancho_prefijo, rect_total.top, ancho_palabra, alto
            )
        return Metricas(fuente, visible, rect_total, rect_palabra)

    def _dibujar_franja(self, descubiertas: list[str]) -> None:
        alto_franja = int(self.alto * tema.ALTURA_FRANJA)
        pygame.draw.rect(self.superficie, tema.FRANJA, (0, 0, self.ancho, alto_franja))
        if not descubiertas:
            return
        fuente = self._fuente(int(self.alto * tema.ALTURA_HISTORIAL))
        contador = self._texto(fuente, str(len(descubiertas)), tema.TEXTO)
        margen = int(self.ancho * 0.02)
        self.superficie.blit(
            contador, contador.get_rect(midright=(self.ancho - margen, alto_franja // 2))
        )
        # Las mas recientes primero, hasta donde alcance el ancho libre.
        libre = self.ancho - contador.get_width() - margen * 3
        x = margen
        for palabra in reversed(descubiertas):
            dibujo = self._texto(fuente, palabra, tema.HISTORIAL)
            paso = dibujo.get_width() + margen
            if x + paso > libre:
                break
            self.superficie.blit(dibujo, dibujo.get_rect(midleft=(x, alto_franja // 2)))
            x += paso

    def _dibujar_cursor(self, respiracion: float) -> None:
        """Invitacion silenciosa a teclear cuando el centro esta vacio."""
        radio = int(self.alto * 0.012 * (0.8 + 0.2 * respiracion))
        capa = pygame.Surface((radio * 2, radio * 2), pygame.SRCALPHA)
        pygame.draw.circle(capa, (*tema.TEXTO_TENUE, 150), (radio, radio), radio)
        self.superficie.blit(
            capa, capa.get_rect(center=(self.ancho // 2, self.alto // 2))
        )

    def dibujar(
        self,
        estado: EstadoTexto,
        celebracion: Celebracion,
        inactivo: bool,
        reloj: float,
    ) -> None:
        self.superficie.fill(tema.FONDO)
        self._dibujar_franja(estado.descubiertas)

        # "Respiracion": presencia suave, sin ruido ni exigir atencion.
        respiracion = (math.sin(reloj * 1.8) + 1.0) / 2.0 if inactivo else 1.0

        medidas = self.metricas(estado)
        if medidas is None:
            self._dibujar_cursor(respiracion)
            pygame.display.flip()
            return

        dibujo = self._texto(medidas.fuente, medidas.texto, tema.TEXTO)
        rect = medidas.rect_total
        if inactivo:
            escala = 0.98 + 0.02 * respiracion
            dibujo = pygame.transform.smoothscale(
                dibujo,
                (max(1, int(rect.width * escala)), max(1, int(rect.height * escala))),
            )
            rect = dibujo.get_rect(center=rect.center)

        if celebracion.activa and medidas.rect_palabra is not None:
            celebracion.dibujar_halo(
                self.superficie,
                self._halo(medidas.fuente, estado.palabra_actual),
                medidas.rect_palabra.center,
            )

        self.superficie.blit(dibujo, rect)
        if celebracion.activa:
            celebracion.dibujar_chispas(self.superficie)
        pygame.display.flip()

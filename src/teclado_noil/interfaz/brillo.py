"""Animacion de celebracion: el resplandor dorado sobre la palabra acertada.

Nunca hay animacion de error. Si Noil rompe la palabra, el resplandor se apaga
con suavidad y en silencio.
"""
from __future__ import annotations

import math
import random

import pygame

from .. import tema

DURACION_ENTRADA = 0.18
DURACION_SOSTEN = 1.5
DURACION_SALIDA = 0.55
DURACION_APAGADO = 0.35  # mas rapido: es el apagon al romper la palabra
CHISPAS_POR_CELEBRACION = 24
# El resplandor se sale de la letra: hay que dejarle sitio alrededor.
MARGEN_HALO = 0.5
# (desenfoque, opacidad, cuanto se abre, cuantas veces se apila) de la capa mas
# difusa a la mas pegada a la letra. Apilar una capa densifica la luz sin
# volverla un bloque plano.
CAPAS_HALO = (
    (12, 0.50, 1.12, 2),
    (7, 0.38, 1.05, 1),
    (4, 0.25, 1.00, 1),
)
# El halo se compone a un tercio de tamano y se amplia al final: es luz
# difusa, no pierde nada, y a pantalla completa evita el tiron de 60 ms que
# se notaba justo al celebrar.
REDUCCION_HALO = 3


def _desenfocar(superficie: pygame.Surface, factor: int) -> pygame.Surface:
    """Desenfoque barato: reducir mucho y volver a ampliar con suavizado."""
    ancho, alto = superficie.get_size()
    chico = pygame.transform.smoothscale(
        superficie, (max(1, ancho // factor), max(1, alto // factor))
    )
    return pygame.transform.smoothscale(chico, (ancho, alto))


def _atenuar(superficie: pygame.Surface, alfa: float) -> pygame.Surface:
    """Baja la opacidad conservando el color, capa por pixel."""
    copia = superficie.copy()
    copia.fill(
        (255, 255, 255, max(0, min(255, int(alfa * 255)))),
        special_flags=pygame.BLEND_RGBA_MULT,
    )
    return copia


class Chispa:
    """Punto de luz dorada que salta de la palabra y se apaga al caer."""

    __slots__ = ("x", "y", "vx", "vy", "vida", "vida_total", "radio")

    def __init__(self, x: float, y: float, radio: float) -> None:
        self.x = x
        self.y = y
        angulo = random.uniform(-math.pi * 0.85, -math.pi * 0.15)
        velocidad = random.uniform(60.0, 190.0)
        self.vx = math.cos(angulo) * velocidad
        self.vy = math.sin(angulo) * velocidad
        self.vida_total = random.uniform(0.7, 1.5)
        self.vida = self.vida_total
        self.radio = radio

    @property
    def viva(self) -> bool:
        return self.vida > 0.0

    def actualizar(self, dt: float) -> None:
        self.vida -= dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += 150.0 * dt  # gravedad suave: las chispas caen al final

    def dibujar(self, destino: pygame.Surface) -> None:
        if not self.viva:
            return
        proporcion = max(0.0, self.vida / self.vida_total)
        radio = max(1, int(self.radio * proporcion))
        aureola = int(radio * 2.2)
        capa = pygame.Surface((aureola * 2, aureola * 2), pygame.SRCALPHA)
        centro = (aureola, aureola)
        pygame.draw.circle(capa, (*tema.BRILLO_BORDE, int(70 * proporcion)), centro, aureola)
        pygame.draw.circle(capa, (*tema.BRILLO, int(240 * proporcion)), centro, radio)
        destino.blit(capa, (int(self.x - aureola), int(self.y - aureola)))


def construir_halo(texto_dorado: pygame.Surface) -> pygame.Surface:
    """Compone el resplandor de una palabra: capas desenfocadas apiladas.

    Es lo caro de la animacion (varios escalados suavizados), asi que se hace
    una sola vez por palabra y la pantalla lo guarda en cache: en pantalla
    completa, recalcularlo en cada fotograma hundia los fotogramas por segundo.
    """
    ancho_final, alto_final = texto_dorado.get_size()
    ancho = max(1, ancho_final // REDUCCION_HALO)
    alto = max(1, alto_final // REDUCCION_HALO)
    reducido = pygame.transform.smoothscale(texto_dorado, (ancho, alto))

    margen = int(alto * MARGEN_HALO)
    lienzo = pygame.Surface((ancho + margen * 2, alto + margen * 2), pygame.SRCALPHA)
    lienzo.blit(reducido, (margen, margen))

    apertura_maxima = max(apertura for _, _, apertura, _ in CAPAS_HALO)
    halo = pygame.Surface(
        (int(lienzo.get_width() * apertura_maxima),
         int(lienzo.get_height() * apertura_maxima)),
        pygame.SRCALPHA,
    )
    centro = halo.get_rect().center
    for factor, peso, apertura, repeticiones in CAPAS_HALO:
        capa = _desenfocar(lienzo, max(2, round(factor / REDUCCION_HALO)))
        if apertura != 1.0:
            capa = pygame.transform.smoothscale(
                capa,
                (int(capa.get_width() * apertura), int(capa.get_height() * apertura)),
            )
        capa = _atenuar(capa, peso)
        posicion = capa.get_rect(center=centro)
        for _ in range(repeticiones):
            halo.blit(capa, posicion)
    return pygame.transform.smoothscale(
        halo,
        (halo.get_width() * REDUCCION_HALO, halo.get_height() * REDUCCION_HALO),
    )


class Celebracion:
    """Estado del resplandor de una palabra. Se reutiliza en cada acierto."""

    def __init__(self) -> None:
        self.tiempo = 0.0
        self.activa = False
        self.apagandose = False
        self.tiempo_apagado = 0.0
        self.intensidad_al_apagar = 0.0
        self.chispas: list[Chispa] = []

    def activar(self, rect: pygame.Rect) -> None:
        """Arranca una celebracion nueva sobre el rectangulo de la palabra."""
        self.tiempo = 0.0
        self.activa = True
        self.apagandose = False
        self.tiempo_apagado = 0.0
        radio = max(3.0, rect.height * 0.03)
        self.chispas = [
            Chispa(
                random.uniform(rect.left, rect.right),
                random.uniform(rect.top + rect.height * 0.25, rect.bottom),
                radio,
            )
            for _ in range(CHISPAS_POR_CELEBRACION)
        ]

    def apagar(self) -> None:
        """Desvanece el resplandor porque la palabra dejo de ser palabra."""
        if self.activa and not self.apagandose:
            self.intensidad_al_apagar = self.intensidad
            self.apagandose = True
            self.tiempo_apagado = 0.0

    @property
    def intensidad(self) -> float:
        """0 a 1: cuanto resplandor dibujar ahora mismo."""
        if not self.activa:
            return 0.0
        if self.apagandose:
            restante = 1.0 - self.tiempo_apagado / DURACION_APAGADO
            return max(0.0, self.intensidad_al_apagar * restante)
        if self.tiempo < DURACION_ENTRADA:
            return self.tiempo / DURACION_ENTRADA
        if self.tiempo < DURACION_ENTRADA + DURACION_SOSTEN:
            # Latido suave mientras se sostiene.
            fase = (self.tiempo - DURACION_ENTRADA) * 4.0
            return 0.82 + 0.18 * math.sin(fase)
        transcurrido = self.tiempo - DURACION_ENTRADA - DURACION_SOSTEN
        return max(0.0, 1.0 - transcurrido / DURACION_SALIDA)

    def actualizar(self, dt: float) -> None:
        if not self.activa:
            return
        self.tiempo += dt
        if self.apagandose:
            self.tiempo_apagado += dt
        for chispa in self.chispas:
            chispa.actualizar(dt)
        self.chispas = [c for c in self.chispas if c.viva]
        if self.intensidad <= 0.0 and not self.chispas:
            self.activa = False

    def dibujar_halo(
        self, destino: pygame.Surface, halo: pygame.Surface, centro: tuple[int, int]
    ) -> None:
        """Pinta el halo ya construido, atenuado segun el latido del momento."""
        intensidad = self.intensidad
        if intensidad <= 0.0:
            return
        capa = _atenuar(halo, intensidad)
        destino.blit(capa, capa.get_rect(center=centro))

    def dibujar_chispas(self, destino: pygame.Surface) -> None:
        """Chispas por delante de la letra, para que se vean saltar."""
        for chispa in self.chispas:
            chispa.dibujar(destino)

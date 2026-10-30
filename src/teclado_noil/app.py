"""Bucle principal del Teclado de Noil."""
from __future__ import annotations

import pygame

from . import audio, config
from .audio.reproductor import Reproductor
from .interfaz.brillo import Celebracion
from .interfaz.pantalla import Pantalla
from .nucleo import progreso
from .nucleo.diccionario import Diccionario, cargar_idioma
from .nucleo.teclado import Tipo, clasificar
from .nucleo.texto import EstadoTexto


class Juego:
    def __init__(self, ajustes: config.Ajustes | None = None) -> None:
        self.ajustes = ajustes or config.AJUSTES

        # Mono a 22 kHz: suficiente para voz, y mucho mas ligero. El buffer
        # pequeno hace que la voz suene en el instante mismo de la tecla.
        pygame.mixer.pre_init(
            audio.FRECUENCIA, -16, audio.CANALES, audio.TAMANO_BUFFER
        )
        pygame.init()

        idioma_ruta = config.DIR_DATOS / f"{self.ajustes.idioma}.json"
        self.idioma = cargar_idioma(idioma_ruta)
        self.diccionario = Diccionario(self.idioma, self.ajustes.nivel_maximo)

        self.pantalla = Pantalla(self.ajustes)
        self.reproductor = Reproductor(
            config.DIR_AUDIO / self.ajustes.idioma, self.ajustes.modo_letra
        )
        self.estado = EstadoTexto()
        self.celebracion = Celebracion()

        self.ruta_progreso = config.ruta_progreso()
        if self.ajustes.guardar_progreso:
            self.estado.descubiertas = progreso.cargar(self.ruta_progreso)

        self.reloj = pygame.time.Clock()
        self.tiempo = 0.0
        self.ultima_pulsacion = 0.0
        self.tiempo_salida = 0.0
        self.corriendo = True

    # -- entrada ---------------------------------------------------------

    def _procesar_tecla(self, evento: pygame.event.Event) -> None:
        # El modificador del evento, no el del teclado ahora: es el que estaba
        # pulsado en el instante de la tecla.
        mods = getattr(evento, "mod", 0)
        # Con Ctrl o Alt nunca se escribe: son combinaciones de adulto.
        if mods & (pygame.KMOD_CTRL | pygame.KMOD_ALT):
            return

        self.ultima_pulsacion = self.tiempo

        if evento.key == pygame.K_ESCAPE:
            return  # ignorada a proposito: Noil no puede salirse
        if evento.key == pygame.K_BACKSPACE:
            if self.estado.retroceso():
                self.reproductor.efecto_retroceso()
                self._revisar_palabra()
            return
        if evento.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            if self.estado.limpiar():
                self.celebracion.apagar()
            return

        pulsacion = clasificar(evento.unicode, self.ajustes.mostrar_digitos)
        if pulsacion.tipo is Tipo.IGNORADA:
            return

        self.estado.escribir(pulsacion.caracter)
        if pulsacion.tipo is Tipo.LETRA:
            self._escribir_letra(pulsacion.caracter)
        elif pulsacion.tipo is Tipo.DIGITO:
            self.reproductor.decir_digito(pulsacion.caracter)
            self.celebracion.apagar()  # el numero corta la palabra
        else:
            self.celebracion.apagar()

    def _escribir_letra(self, caracter: str) -> None:
        """Decide de una vez que se oye y que se ve al pulsar una letra.

        Hay que saber si la palabra quedo completa antes de reproducir nada:
        si quedo, la voz dice "o... gato" en un solo canal, en lugar de
        encimar el nombre de la letra con la palabra.
        """
        letra = self.idioma.letras.get(caracter)
        palabra = self.diccionario.buscar(self.estado.palabra_actual)
        medidas = self.pantalla.metricas(self.estado)
        rect = medidas.rect_palabra if medidas else None

        if palabra is None or rect is None:
            self.celebracion.apagar()  # se apaga en silencio, nunca hay error
            if letra:
                self.reproductor.decir_letra(letra)
            return

        self.celebracion.activar(rect)
        if letra:
            self.reproductor.decir_letra_y_palabra(letra, palabra)
        else:
            self.reproductor.decir_palabra(palabra)
        ya_estaba = palabra.texto in self.estado.descubiertas
        self.estado.registrar_descubierta(palabra.texto)
        if self.ajustes.guardar_progreso and not ya_estaba:
            progreso.guardar(self.ruta_progreso, self.estado.descubiertas)

    def _revisar_palabra(self) -> None:
        """Tras borrar: si lo que queda ya no es palabra, se apaga el brillo."""
        if self.diccionario.buscar(self.estado.palabra_actual) is None:
            self.celebracion.apagar()

    def _revisar_salida(self, dt: float) -> None:
        """Salida de adultos: Ctrl+Shift+Q sostenido."""
        mods = pygame.key.get_mods()
        teclas = pygame.key.get_pressed()
        combinacion = (
            mods & pygame.KMOD_CTRL and mods & pygame.KMOD_SHIFT and teclas[pygame.K_q]
        )
        self.tiempo_salida = self.tiempo_salida + dt if combinacion else 0.0
        if self.tiempo_salida >= self.ajustes.segundos_salida:
            self.corriendo = False

    # -- bucle -----------------------------------------------------------

    def ejecutar(self) -> None:
        while self.corriendo:
            dt = self.reloj.tick(self.ajustes.fps) / 1000.0
            self.tiempo += dt

            for evento in pygame.event.get():
                if evento.type == pygame.QUIT:
                    continue  # Alt+F4 ignorado: solo sale la combinacion secreta
                if evento.type == pygame.KEYDOWN:
                    self._procesar_tecla(evento)

            self._revisar_salida(dt)
            self.celebracion.actualizar(dt)
            inactivo = (
                self.tiempo - self.ultima_pulsacion > self.ajustes.segundos_inactividad
            )
            self.pantalla.dibujar(self.estado, self.celebracion, inactivo, self.tiempo)

        if self.ajustes.guardar_progreso:
            progreso.guardar(self.ruta_progreso, self.estado.descubiertas)
        pygame.quit()


def main() -> None:
    Juego().ejecutar()

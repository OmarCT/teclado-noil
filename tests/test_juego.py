"""Pruebas del flujo completo, con la pantalla y el audio simulados.

Lo que se comprueba aqui es la experiencia: que celebrar, cuando apagarse y
que nunca haya castigo por equivocarse.
"""
import os

import pytest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame  # noqa: E402

from teclado_noil import config  # noqa: E402
from teclado_noil.app import Juego  # noqa: E402
from teclado_noil.audio import nombres, reproductor  # noqa: E402
from teclado_noil.interfaz.pantalla import Pantalla, modo_video  # noqa: E402


@pytest.fixture
def juego():
    partida = Juego(
        config.Ajustes(
            pantalla_completa=False,
            tamano_ventana=(1280, 720),
            guardar_progreso=False,
        )
    )
    yield partida
    pygame.quit()


def teclear(juego, cadena, mod=0):
    for caracter in cadena:
        clave = pygame.K_SPACE if caracter == " " else ord(caracter.lower())
        juego._procesar_tecla(
            pygame.event.Event(pygame.KEYDOWN, key=clave, unicode=caracter, mod=mod)
        )


def pulsar(juego, clave, mod=0):
    juego._procesar_tecla(pygame.event.Event(pygame.KEYDOWN, key=clave, unicode="", mod=mod))


def test_una_palabra_real_enciende_el_brillo_y_entra_al_historial(juego):
    teclear(juego, "GATO")
    assert juego.celebracion.activa
    assert juego.estado.descubiertas == ["GATO"]


def test_el_brillo_entra_progresivamente_no_de_golpe(juego):
    teclear(juego, "GATO")
    assert juego.celebracion.intensidad == 0.0  # arranca apagado
    juego.celebracion.actualizar(0.09)
    a_mitad = juego.celebracion.intensidad
    juego.celebracion.actualizar(0.09)
    assert 0.0 < a_mitad < juego.celebracion.intensidad


def test_romper_la_palabra_apaga_el_brillo_sin_castigo(juego):
    teclear(juego, "GATOX")
    assert juego.celebracion.apagandose
    assert juego.estado.contenido == "GATOX"  # lo escrito se queda, no se borra


def test_seguir_escribiendo_puede_dar_un_segundo_acierto(juego):
    teclear(juego, "PAN")
    assert juego.estado.descubiertas == ["PAN"]
    teclear(juego, "ZA")  # PANZA tambien es palabra
    assert juego.estado.descubiertas == ["PAN", "PANZA"]
    assert not juego.celebracion.apagandose


def test_un_digito_corta_la_palabra(juego):
    teclear(juego, "SOL")
    assert juego.celebracion.activa
    teclear(juego, "7")
    assert juego.celebracion.apagandose
    assert juego.estado.palabra_actual == ""


def test_el_espacio_empieza_palabra_nueva(juego):
    teclear(juego, "SOL LUNA")
    assert juego.estado.descubiertas == ["SOL", "LUNA"]


def test_enter_limpia_el_centro_pero_no_el_historial(juego):
    teclear(juego, "LUNA")
    pulsar(juego, pygame.K_RETURN)
    assert juego.estado.contenido == ""
    assert juego.estado.descubiertas == ["LUNA"]


def test_escape_no_hace_nada(juego):
    teclear(juego, "SOL")
    pulsar(juego, pygame.K_ESCAPE)
    assert juego.estado.contenido == "SOL"
    assert juego.corriendo


def test_retroceso_borra_una_letra(juego):
    teclear(juego, "SOLX")
    pulsar(juego, pygame.K_BACKSPACE)
    assert juego.estado.contenido == "SOL"


def test_ctrl_mas_letra_no_escribe(juego):
    teclear(juego, "Q", mod=pygame.KMOD_LCTRL)
    assert juego.estado.contenido == ""


def test_el_brillo_se_coloca_sobre_la_palabra_no_sobre_toda_la_linea(juego):
    teclear(juego, "XJK LUNA")
    medidas = juego.pantalla.metricas(juego.estado)
    assert medidas.rect_palabra is not None
    assert medidas.rect_palabra.width < medidas.rect_total.width
    assert medidas.rect_palabra.right == pytest.approx(medidas.rect_total.right, abs=6)


def test_las_palabras_descubiertas_no_se_duplican(juego):
    teclear(juego, "SOL SOL")
    assert juego.estado.descubiertas == ["SOL"]


class TestModoVideo:
    """La pantalla completa es como arranca para Noil: tiene que abrir siempre."""

    def test_pantalla_completa_pide_un_tamano_real(self):
        """SDL rechaza un modo de 0x0, asi que nunca hay que pedirselo."""
        pygame.display.init()
        tamano, banderas = modo_video(config.Ajustes(pantalla_completa=True))
        assert banderas & pygame.FULLSCREEN
        assert tamano == pygame.display.get_desktop_sizes()[0]
        assert all(dimension > 0 for dimension in tamano)

    def test_en_ventana_manda_el_tamano_de_los_ajustes(self):
        tamano, banderas = modo_video(
            config.Ajustes(pantalla_completa=False, tamano_ventana=(800, 600))
        )
        assert tamano == (800, 600)
        assert not banderas & pygame.FULLSCREEN

    def test_la_ventana_de_verdad_abre_en_pantalla_completa(self):
        pantalla = Pantalla(config.Ajustes(pantalla_completa=True))
        try:
            assert pantalla.ancho > 0 and pantalla.alto > 0
        finally:
            pygame.display.quit()


class TestVoz:
    """Nunca deben oirse dos voces a la vez."""

    @staticmethod
    def _hay_voz(juego):
        if not juego.reproductor.disponible:
            pytest.skip("sin mezclador de audio en este entorno")
        return pygame.mixer.Channel(reproductor.CANAL_VOZ)

    def test_la_palabra_se_encola_detras_de_la_letra(self, juego):
        """Al completar GATO se oye "o... gato", no las dos cosas encimadas."""
        canal = self._hay_voz(juego)
        teclear(juego, "GATO")
        clip_palabra = juego.reproductor._cargar(nombres.archivo_palabra("GATO"))
        clip_letra = juego.reproductor._cargar(nombres.archivo_letra("O", "nombre"))
        assert canal.get_sound() is clip_letra      # suena la letra
        assert canal.get_queue() is clip_palabra    # y la palabra espera turno

    def test_al_acertar_se_omite_la_silaba_de_la_letra(self, juego):
        """"ele... la... sol" serian tres clips y solo caben dos en la cola."""
        canal = self._hay_voz(juego)
        teclear(juego, "SOL")
        assert canal.get_queue() is juego.reproductor._cargar(
            nombres.archivo_palabra("SOL")
        )

    def test_una_letra_normal_no_deja_nada_sonando_en_otro_canal(self, juego):
        canal = self._hay_voz(juego)
        teclear(juego, "G")
        assert canal.get_busy()
        otros = [
            indice
            for indice in range(pygame.mixer.get_num_channels())
            if indice != reproductor.CANAL_VOZ
            and pygame.mixer.Channel(indice).get_busy()
        ]
        assert otros == []

    def test_la_siguiente_letra_corta_a_la_anterior(self, juego):
        """La respuesta a la ultima tecla es lo que importa."""
        canal = self._hay_voz(juego)
        teclear(juego, "G")
        primera = canal.get_sound()
        teclear(juego, "T")
        assert canal.get_sound() is not primera

    def test_el_retroceso_suena_fuera_del_canal_de_voz(self, juego):
        """Es un ruidito, no una voz: no debe cortar lo que se este diciendo."""
        self._hay_voz(juego)
        teclear(juego, "A")
        pulsar(juego, pygame.K_BACKSPACE)
        assert pygame.mixer.Channel(reproductor.CANAL_EFECTOS).get_busy()

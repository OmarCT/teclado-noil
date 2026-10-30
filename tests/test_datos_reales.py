"""El archivo de vocabulario que se entrega debe ser tecleable por Noil."""
import re

import pytest

from teclado_noil import config
from teclado_noil.nucleo.diccionario import Diccionario, cargar_idioma
from teclado_noil.nucleo.texto import LETRAS_VALIDAS


@pytest.fixture(scope="module")
def idioma():
    return cargar_idioma(config.DIR_DATOS / "es.json")


def test_todas_las_palabras_se_pueden_teclear(idioma):
    """Solo A-Z y enie: lo demas Noil no lo podria escribir nunca."""
    invalidas = [
        p.texto for p in idioma.palabras
        if not re.fullmatch(r"[A-ZÑ]+", p.texto)
    ]
    assert invalidas == []


def test_ninguna_palabra_es_mas_corta_que_el_minimo(idioma):
    cortas = [p.texto for p in idioma.palabras if len(p.texto) < idioma.longitud_minima]
    assert cortas == []


def test_no_hay_palabras_repetidas(idioma):
    textos = [p.texto for p in idioma.palabras]
    assert len(textos) == len(set(textos))


def test_estan_las_27_letras_del_abecedario(idioma):
    assert set(idioma.letras) == set(LETRAS_VALIDAS)
    assert len(idioma.letras) == 27


def test_cada_letra_tiene_nombre(idioma):
    """El sonido es opcional; el nombre nunca."""
    for letra in idioma.letras.values():
        assert letra.nombre


def test_estan_los_diez_digitos(idioma):
    assert sorted(idioma.digitos) == [str(d) for d in range(10)]


def test_la_familia_esta_en_el_nivel_activo(idioma):
    diccionario = Diccionario(idioma, nivel_maximo=1)
    for nombre in ("NOIL", "OMAR", "GUADALUPE", "ELENA", "LUPITA", "BERTHA"):
        assert diccionario.buscar(nombre) is not None, nombre


def test_el_nivel_uno_tiene_vocabulario_suficiente(idioma):
    assert len(Diccionario(idioma, nivel_maximo=1)) > 300


def test_ningun_sonido_de_letra_se_lee_como_sigla(idioma):
    """El sintetizador lee "mmm" como "triple eme", no como un sonido.

    Cualquier letra repetida tres veces vuelve a caer en la misma trampa.
    """
    import re

    sospechosos = [
        (simbolo, letra.sonido)
        for simbolo, letra in idioma.letras.items()
        if letra.sonido and re.search(r"(.)\1\1", letra.sonido)
    ]
    assert sospechosos == []


def test_las_vocales_solo_dicen_su_nombre(idioma):
    """Una vocal ya suena como se llama: repetirlo seria "a... a"."""
    for vocal in "AEIOU":
        assert idioma.letras[vocal].sonido == ""

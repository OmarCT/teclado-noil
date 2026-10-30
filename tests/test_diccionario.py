import json

import pytest

from teclado_noil.nucleo.diccionario import Diccionario, cargar_idioma


@pytest.fixture
def idioma(tmp_path):
    datos = {
        "idioma": "es",
        "etiqueta": "prueba",
        "voz_tts": "es-MX-DaliaNeural",
        "longitud_minima": 3,
        "letras": {"A": {"nombre": "a", "sonido": "aaa"}},
        "digitos": {"7": {"nombre": "siete"}},
        "palabras": [
            {"texto": "SOL", "nivel": 1},
            {"texto": "SOLA", "nivel": 1},
            {"texto": "MAMA", "nivel": 1, "pronunciacion": "mamá"},
            {"texto": "NOIL", "nivel": 1, "nombre_propio": True},
            {"texto": "DINOSAURIO", "nivel": 2},
            {"texto": "NO", "nivel": 1},
        ],
    }
    ruta = tmp_path / "es.json"
    ruta.write_text(json.dumps(datos, ensure_ascii=False), encoding="utf-8")
    return cargar_idioma(ruta)


def test_encuentra_una_palabra_del_nivel_activo(idioma):
    assert Diccionario(idioma, 1).buscar("SOL").texto == "SOL"


def test_ignora_el_nivel_todavia_cerrado(idioma):
    assert Diccionario(idioma, 1).buscar("DINOSAURIO") is None
    assert Diccionario(idioma, 2).buscar("DINOSAURIO").texto == "DINOSAURIO"


def test_respeta_la_longitud_minima(idioma):
    assert Diccionario(idioma, 1).buscar("NO") is None


def test_lo_tecleado_sin_acentos_encuentra_la_palabra(idioma):
    assert Diccionario(idioma, 1).buscar("mamá").texto == "MAMA"
    assert Diccionario(idioma, 1).buscar("MAMA").texto == "MAMA"


def test_el_tts_lee_la_grafia_con_acento(idioma):
    diccionario = Diccionario(idioma, 1)
    assert diccionario.buscar("MAMA").para_decir == "mamá"
    assert diccionario.buscar("SOL").para_decir == "sol"


def test_una_palabra_desconocida_no_es_acierto(idioma):
    assert Diccionario(idioma, 1).buscar("XQZK") is None


def test_seguir_escribiendo_puede_dar_otro_acierto(idioma):
    """S-O-L celebra, y la A de SOLA celebra otra vez."""
    diccionario = Diccionario(idioma, 1)
    assert diccionario.buscar("SOL") is not None
    assert diccionario.buscar("SOLA") is not None

from teclado_noil.nucleo.texto import EstadoTexto, normalizar


def test_normalizar_quita_acentos_y_sube_a_mayuscula():
    assert normalizar("mamá") == "MAMA"
    assert normalizar("avión") == "AVION"
    assert normalizar("gato") == "GATO"


def test_normalizar_conserva_la_enie():
    assert normalizar("niño") == "NIÑO"
    assert normalizar("Ñ") == "Ñ"


def test_normalizar_quita_la_dieresis():
    assert normalizar("pingüino") == "PINGUINO"


class TestPalabraActual:
    def test_son_las_letras_finales(self):
        estado = EstadoTexto()
        for caracter in "GATO":
            estado.escribir(caracter)
        assert estado.palabra_actual == "GATO"

    def test_el_espacio_empieza_palabra_nueva(self):
        estado = EstadoTexto()
        for caracter in "SOL LU":
            estado.escribir(caracter)
        assert estado.palabra_actual == "LU"

    def test_el_digito_corta_la_palabra_igual_que_un_espacio(self):
        estado = EstadoTexto()
        for caracter in "PAN7":
            estado.escribir(caracter)
        assert estado.palabra_actual == ""

    def test_vacia_al_principio(self):
        assert EstadoTexto().palabra_actual == ""


def test_retroceso_borra_una_letra_y_avisa_si_no_habia_nada():
    estado = EstadoTexto()
    estado.escribir("A")
    assert estado.retroceso() is True
    assert estado.contenido == ""
    assert estado.retroceso() is False


def test_limpiar_vacia_el_centro_pero_conserva_el_historial():
    estado = EstadoTexto()
    estado.escribir("A")
    estado.registrar_descubierta("SOL")
    assert estado.limpiar() is True
    assert estado.contenido == ""
    assert estado.descubiertas == ["SOL"]


def test_el_historial_no_repite_palabras():
    estado = EstadoTexto()
    estado.registrar_descubierta("SOL")
    estado.registrar_descubierta("SOL")
    assert estado.descubiertas == ["SOL"]


def test_visible_recorta_lo_que_no_cabe_en_pantalla():
    estado = EstadoTexto()
    for caracter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        estado.escribir(caracter)
    assert len(estado.visible) == 14
    assert estado.visible.endswith("Z")

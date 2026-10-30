from teclado_noil.nucleo.teclado import Tipo, clasificar


def test_las_minusculas_se_muestran_en_mayuscula():
    pulsacion = clasificar("a")
    assert pulsacion.tipo is Tipo.LETRA
    assert pulsacion.caracter == "A"


def test_shift_no_cambia_nada():
    assert clasificar("A").caracter == clasificar("a").caracter


def test_acepta_la_enie():
    assert clasificar("ñ") == clasificar("Ñ")
    assert clasificar("ñ").caracter == "Ñ"


def test_las_vocales_con_acento_valen_como_la_vocal():
    assert clasificar("á").caracter == "A"


def test_el_espacio_separa():
    assert clasificar(" ").tipo is Tipo.ESPACIO


def test_los_digitos_se_aceptan_o_se_bloquean():
    assert clasificar("7", aceptar_digitos=True).tipo is Tipo.DIGITO
    assert clasificar("7", aceptar_digitos=False).tipo is Tipo.IGNORADA


def test_los_simbolos_se_ignoran():
    for caracter in ("@", "-", "+", "\x11", "\t", ""):
        assert clasificar(caracter).tipo is Tipo.IGNORADA, caracter

"""Paleta y tipografia. Cambia los colores aqui y cambia toda la app."""
from __future__ import annotations

# Tonos calidos: nada de blanco puro ni negro puro.
CREMA = (255, 244, 230)
CREMA_OSCURO = (247, 230, 206)
CHOCOLATE = (92, 64, 51)
CHOCOLATE_TENUE = (168, 140, 124)
AMBAR = (255, 179, 71)
DORADO = (255, 215, 0)
DURAZNO = (255, 205, 160)
VERDE_SUAVE = (138, 176, 128)

FONDO = CREMA
TEXTO = CHOCOLATE
TEXTO_TENUE = CHOCOLATE_TENUE
BRILLO = DORADO
BRILLO_BORDE = AMBAR
HISTORIAL = CHOCOLATE_TENUE
FRANJA = CREMA_OSCURO

# Andika (SIL, licencia OFL) esta pensada para lectores principiantes.
# Si el archivo no esta, se usa la fuente por defecto de pygame.
FUENTE_ARCHIVO = "Andika-Bold.ttf"

# Fracciones de la altura de pantalla, para que escale en cualquier monitor.
ALTURA_LETRA = 0.42
ALTURA_LETRA_MINIMA = 0.12
ALTURA_HISTORIAL = 0.045
ALTURA_FRANJA = 0.12

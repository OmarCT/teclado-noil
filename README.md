# Teclado de Noil

Un teclado que ensena las letras. Para Noil, de 3 anos.

Noil aplasta una tecla y la letra aparece enorme en la pantalla mientras una voz
le dice como se llama y como suena: *"eme... ma"*. Cuando lo que escribe forma
una palabra de verdad — `G`, `A`, `T`, `O` — la palabra se enciende en dorado,
saltan chispas y la voz dice **gato**, justo despues de la ultima letra.

Nunca se le dice que se equivoco. Si la palabra se rompe, la luz simplemente se
apaga.

## Para jugar

```bash
uv venv
uv pip install -e ".[dev]"
.venv/bin/python main.py
```

Tiene que ser el Python del entorno, no el del sistema: `python main.py` a
secas falla con `No module named 'pygame'`. Con `source .venv/bin/activate`
basta `python main.py`.

Sale con **Ctrl + Shift + Q** mantenido dos segundos. `Esc` y `Alt+F4` no hacen
nada: son para que Noil no se salga solo.

| Tecla | Que hace |
|---|---|
| `A`–`Z`, `Ñ` | Escribe la letra y la dice |
| `0`–`9` | Dice el numero y empieza palabra nueva |
| `Espacio` | Separa palabras |
| `Retroceso` | Borra una letra |
| `Enter` | Limpia la pantalla (el historial se queda) |

## Para el .exe

```bash
python scripts/empaquetar.py             # un solo .exe
python scripts/empaquetar.py --carpeta   # una carpeta que arranca al instante
```

Deja el resultado en `dist/`, con los datos, la voz y la fuente dentro. No
necesita internet.

El archivo unico pesa unos 52 MB y los descomprime en cada arranque, asi que
tarda unos segundos en abrir. La version en carpeta abre de inmediato: para
Noil conviene esa, con un acceso directo al `.exe` de dentro en el escritorio.

## Para cambiar cosas

- **Agregar palabras** (nombres de la familia, lo que sea): `datos/es.json`.
  Luego `python scripts/generar_audio.py` para la voz nueva, y
  `python scripts/revisar_audio.py` para ver si alguna salio deletreada. Si
  alguna suena mal, dale otra grafia en el campo `pronunciacion` (a veces basta
  poner o quitar una tilde) y regenera con `--forzar --solo palabras`.
- **Abrir mas vocabulario** cuando crezca: `nivel_maximo = 2` en
  `src/teclado_noil/config.py`.
- **Colores**: `src/teclado_noil/tema.py`.
- **Poner tu propia voz**: graba y sobrescribe el `.wav` que quieras en
  `assets/audio/es/`.

## Creditos

Fuente [Andika](https://software.sil.org/andika/) de SIL International, bajo
SIL Open Font License 1.1. Voz generada con
[edge-tts](https://github.com/rany2/edge-tts) (es-MX).

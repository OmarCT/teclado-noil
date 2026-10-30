# Teclado de Noil

Aplicacion de escritorio para que Noil, de 3 anos, aprenda las letras tecleando.
Pulsa una tecla, aparece la letra enorme y la oye; cuando lo que escribe forma
una palabra real, la palabra brilla y se escucha.

## El usuario manda sobre el codigo

Noil tiene 3 anos. Ante cualquier duda de diseno, gana lo que funcione para el:

- **Nunca se le dice que se equivoco.** No hay sonidos de error, ni cruces, ni
  texto rojo, ni nada que se borre solo. Si rompe una palabra, el brillo se
  apaga con suavidad y en silencio.
- **Respuesta inmediata.** Cada tecla suena al instante. Por eso las letras se
  interrumpen entre si y por eso los clips van recortados de silencio.
- **Nunca dos voces a la vez.** Toda la voz va por un solo canal. Al completar
  una palabra se oye "o... gato", con la palabra encolada detras del nombre de
  su ultima letra; antes sonaban encimadas y no se entendia ninguna.
- **Letras enormes.** Vale mas una letra que llene la pantalla que mucho texto.
- **No puede salirse ni romper nada.** Pantalla completa, `Esc` y `Alt+F4`
  ignorados, y una combinacion de adulto para cerrar.
- **Nada de leer para usarla.** Ningun menu, ningun boton, ningun texto de
  instrucciones: la app se entiende aplastando teclas.

## Como se corre

```bash
uv venv && uv pip install -e ".[dev]"      # preparar el entorno
.venv/bin/python main.py                   # jugar
.venv/bin/python -m pytest -q              # pruebas (solo logica, sin render)
.venv/bin/python scripts/generar_audio.py  # generar la voz que falte
.venv/bin/python scripts/empaquetar.py     # construir el .exe (en Windows)
```

Siempre el Python del entorno. El del sistema aqui es un pyenv 3.14 sin
pygame, y `python main.py` falla; `main.py` detecta ese caso y lo explica.

Para desarrollar sin pantalla completa, cambia `pantalla_completa` en
`src/teclado_noil/config.py`, o usa `Ajustes(pantalla_completa=False)`.

## Como esta organizado

```
main.py                     punto de entrada
datos/es.json               vocabulario, letras y digitos del espanol
assets/audio/es/            un .wav por letra, digito y palabra
assets/fuentes/             Andika (SIL, licencia OFL)
src/teclado_noil/
  config.py                 rutas y ajustes (nivel, idioma, pantalla completa)
  tema.py                   colores y tamanos
  app.py                    bucle principal: eventos -> estado -> dibujo
  nucleo/                   logica pura, sin pygame: lo unico que se prueba
    texto.py                normalizacion y estado de lo escrito
    diccionario.py          carga del idioma y busqueda de palabras
    teclado.py              que hacer con cada pulsacion
    progreso.py             palabras descubiertas entre sesiones
  audio/reproductor.py      la voz (un canal) y los efectos (otro)
  interfaz/pantalla.py      dibujado
  interfaz/brillo.py        animacion de celebracion
scripts/generar_audio.py    sintesis de voz con edge-tts
scripts/revisar_audio.py    busca clips que el TTS leyo deletreando
scripts/empaquetar.py       PyInstaller
```

`nucleo/` no importa pygame nunca: es lo que mantiene las pruebas rapidas y
honestas. La regla al agregar codigo: si se puede decidir sin pintar nada,
va en `nucleo/`.

## Decisiones ya tomadas (y por que)

- **pygame-ce, no customtkinter.** La app es texto gigante, luz y sonido: no
  tiene widgets. Lo que si necesita es un bucle a 60 fps y control fino del
  audio.
- **Todo en mayusculas.** Es la forma que Noil ve en sus libros y en las teclas
  del teclado. Shift no cambia nada: lo que pulsa es lo que ve.
- **Nombre y sonido de cada letra** ("eme... ma"). El sonido es lo que permite
  descubrir que las letras construyen palabras; el nombre es lo que se le
  pregunta en la escuela. Se configura con `modo_letra`.
  El sonido es la silaba con A, como se ensena en preescolar, y no el fonema
  aislado: escrito "mmm", el sintetizador lo lee como una sigla ("triple
  eme"), y no acepta SSML fonetico para pedirselo de otra forma. Las vocales
  y la H, W y X se quedan solo con el nombre, con el campo `sonido` vacio.
- **Palabra detectada en cada tecla**, sobre lo escrito desde el ultimo espacio
  o digito. No hay que pulsar nada para confirmar: a los 3 anos ese paso extra
  no se entiende. Si sigue escribiendo y sale otra palabra, celebra otra vez.
- **Lista curada, no diccionario completo.** Con un diccionario del espanol
  saldrian aciertos constantes por azar (y palabras que no queremos). Las
  palabras estan en `datos/es.json`, por nivel: `1` lo que Noil ya conoce,
  `2` vocabulario de 3 a 5 anos. Se abre subiendo `nivel_maximo` en
  `config.py`. La familia (Noil, Omar, Guadalupe, Elena...) esta en el nivel 1.
- **Acentos en el dato, no en la pantalla.** El texto se guarda sin tilde
  (`MAMA`, porque es lo que puede teclear) y el campo `pronunciacion` lleva la
  grafia real (`mamá`) para que la voz la lea bien. Sirve igual para los
  apodos: `LUFY` se pronuncia `lufi`.
- **Voz generada una vez, guardada en el repo.** `edge-tts` necesita internet;
  los clips versionados hacen que el `.exe` funcione siempre, sin conexion.
  Cualquier clip se puede reemplazar por una grabacion real sobrescribiendo el
  archivo: la app no distingue de donde salio.
- **Las grafias que se le dan al TTS son prueba y error.** Cuando edge-tts no
  reconoce una grafia, la deletrea: "Nóil" sonaba "ene-oil", "cu" (el nombre
  de la Q) y "ba" salian deletreadas. Las tildes no siguen regla: a "Nóil" le
  sobraba y a "cú", "cé" y "bá" les hacia falta. Por eso esta
  `scripts/revisar_audio.py`, que compara cada clip con lo que deberia durar
  un texto de ese largo y delata los deletreos sin tener que escuchar los 763
  uno por uno. Hay que correrlo despues de agregar palabras.
- **Clips recortados de silencio y en mono a 22 kHz.** edge-tts devuelve casi
  dos segundos de silencio por clip; sin recortar, Noil nunca oiria una letra
  entera antes de pulsar la siguiente.
- **Progreso en un JSON, no en una base de datos.** Esto es un juguete.
- **Sin imagenes en esta version.** La celebracion es brillo y voz.
- **El empaquetado necesita `--paths src`.** `main.py` agrega `src/` al
  `sys.path` en tiempo de ejecucion, pero PyInstaller analiza los imports de
  forma estatica: sin ese argumento no encuentra `teclado_noil` y el ejecutable
  muere con `ModuleNotFoundError`. Lo mismo vale para cualquier modulo que se
  importe de forma dinamica mas adelante.
- **La tecla Windows no se bloquea.** Bloquearla de verdad exige un hook de
  teclado de bajo nivel de Windows, que es fragil y lo que usan los keyloggers.
  El resto del encierro (pantalla completa, `Esc`, `Alt+F4`) si esta.

## Estilo

Codigo y comentarios en espanol, sin acentos en el codigo fuente. Nombres
descriptivos (`palabra_actual`, no `pa`). Comentarios solo donde la razon no se
ve en el codigo; las decisiones de arriba ya estan explicadas aqui.

## Lo que viene despues (no ahora)

Ingles con la traduccion al espanol en pantalla (por eso el idioma ya sale de
`datos/<codigo>.json` y de `assets/audio/<codigo>/`, y `Palabra` ya tiene campo
`traduccion`); trazado de letras si algun dia hay pantalla tactil; pantalla de
estadisticas para los papas; emoji o ilustracion por palabra; hook de bajo
nivel para la tecla Windows.

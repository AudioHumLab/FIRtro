# Volumen de MPD ligado a FIRtro

## Necesidad:

Se quiere que el cliente MPD favorito del usuario pueda gobernar y conocer el volumen en FIRtro. 

Y a la inversa, si cambiamos el volumen en FIRtro, cualquier cliente MPD deberá reflejarlo.

## Consideraciones

El volumen de MPD es 0-100 

FIRtro dispone de:
1. **`gain`**: es la ganancia absoluta de salida del convolver
2. **`level`**: es el volumen calibrado para un cierto SPL de referencia en sala (level = 0 dB). Los cambios de volumen del usuario se operan normalmente sobre `level`.

## Solución propuesta: 

MPD permite configurar un fake mixer de manera que no se aplica a la salida hacia FIRtro (salida a JACK), pero el ajuste de volumen puede así ser leido por un cliente externo al objeto de gobernar un sistema de control de volumen externo como un amplificador o, en nuestro caso, FIRtro.

## Servicios disponibles:

### FIRtro

El arranque de FIRtro (`initfirtro.py`) arranca el **`server.py`** que queda corriendo en memoria para atender órdenes vía tcp puerto 9999, y después, gracias al módulo auxiliar `client.py`, initfirtro.py puede comunicarse con el server para ajustar FIRtro al arranque.

El shell de usuario o la página web de control mandan las órdenes a FIRtro con la orden del shell `control` (que es un wrapper de `echo "comando argumentos" | netcat localhost 9999`). La orden será atendida por `server.py`.

### MPD
El server MPD atiende órdenes por tcp puerto 6600, de forma standard.

## Implementación 

### MPD -->>-- FIRtro

Nuevo módulo residente **`client_mpd.py`** que escuchará al server MPD y en caso de detectar un cambio de volumen, lo trasladará a FIRtro.

### MPD --<<-- FIRtro

El módulo `server_process.py` de FIRtro actualizará el 'volume' de MPD cuando el usuario reajuste el 'level' de FIRtro. Basta con cargar `client_mpd` en server_process.py para poder actualizar a MPD.

**NOTA:** aunque la opción `mpd_volume_linked2firtro = False` en `audio/config` los cambios de nivel en FIRtro se verán reflejados en el indicador de volumen del cliente MPD.

### Protección antibucle

Los cambios en MPD se traducen por parte de `client_mpd.py` en términos de `gain` en FIRtro.

FIRtro habla con MPD solo cuando hay cambios ordinarios de `level`, no habla ante cambios directos de gain por parte del usuario, ya que son cambios ajenos a un uso normal del sistema.

Por tanto no hay bucle.

Sin embargo, un ajuste ordinario de `level` por parte del usuario, será propagado a MPD y será acusado de vuelta en el daemon `client_mpd.py` que generará un nuevo ajuste `gain` en el sistema. Se puede visualizar en la 'consola de FIRtro' (en los printados del terminal que corre `server_process.py`). Este ajuste repetido es inocuo, pero se ha incluido un temporizador en `server_process.py` para evitarlo.

### Efectos colaterales

Si usamos `client_mpd` se observan efectos colaterales en Pulseaudio debido a que éste automágicamente se linka con MPD y cambia el volumen del `jack_sink` a la vez que se produzcan cambios en el fake volumen de mpd :-/

WORK IN PROGRESS: anular la carga automágica del módulo mpd de Pulseaudio.

## Cambios

- `/etc/modules`

Se incluye **snd_dummy**

- `home/USER/.mpdconf`

Se descarta `mixer_type = null` no funciona en la salida jack:

    audio_output{type "jack" .... .... mixer_type  "null"}

Se usa:

    audio_output {
        type            "alsa"
        name            "alsa_dummy"
        mixer_type      "hardware"
        mixer_device    "hw:Dummy"
        mixer_control   "Master"
    }

Fuentes: apuntes de **rripio** y https://github.com/therealmuffin/synchronator/blob/master/INSTALL_MANUAL.md

- `audio/config`, `getconfig.py` 

Se incluye la opción `mpd_volume_linked2firtro = True|False`

- `client_mpd.py`

Nuevo script daemon, incluye `import client.py` para hablar con FIRtro.

- `ìnitfirtro.py`, `stopfirtro.py`

Gestión de `client_mpd.py`

- `server_process.py`

Se incluye `import client_mpd` para hablar con MPD cuando el usuario reajusta 'level'

- `python-mpd`

Nuevo paquete Debian a instalar.



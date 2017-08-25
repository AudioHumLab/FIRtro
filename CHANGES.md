## 2017-mayo. Cambios:

- Revisión de la gestión de curvas target "System EQ". Se computa el RoomGain positivo. Se baja el volumen si se quiere reactivar SysEQ cuando no hay headroom. Implementado en **curves.py** y en la máquina de control de volumen en **server_process.py**. El estado de SysEQ se traslada a audio/status. Al arranque se usará la configuración de SysEQ definida en lspk/altavoz/speaker.

- Se añade **'gmax'** en audio/config, define el tope de ganancia admitida en Brutefir, normalemnte 0. Relacionado con la revisión de la máquina de control de volumen en server_process.py.

(Ver detalles en **dov/dev/VolumeMachine.md**).

- Ajuste de tonos defeatable al arranque, mediante opción en audio/config.

- Elección del resampler (alsa_in/out o zita-ajbridge) para tarjetas externas en audio/config.

- Reordenación de secciones [xxxx EQ] en la estructura 'ini' del archivo de estado (audio/status). Se incluye el alcance de SysEQ (Room Gain y House Curve). Se muestra en la consola de FIRtro (sección 'if control_output ...' de server_process.py).

- Se integra el PEQ en las página DRC de la web (switch y gráficas).

- Se reordena la parrilla informativa de la página principal 'Volume' de la web.

- Rutina auxiliar wait4.py para comprobar la ejecución de programas, se usa en initfirtro.py y sustituye las esperas estáticas time.sleep(xx).

- Simplificación de mplayer_options en audio/config. Se arranca mplayer sin puertos de destino en jack para no solapar a otra fuente en el arranque.

- Mejoras en la gestión de canales TDT por su nombre.

- Script de resintonización de la TDT con reconexión en jack si la entrada actual es TDT.

## 2017-agosto. Adaptaciones para compatibilidad con Debian 9.1:

- La instalación Debian sin escritorio viene sin archivo de configuración de dbus en `/etc/dbus-1/`, se proporciona indicación en la wiki.
 
- Se detecta que no se libera la conexión con server.py:

    Se revisa el lanzamiento de server.py en initfirtro. 
    
    Se reemplaza en los scripts el uso de subprocesos Popen shell=True para conectar con el server y con Brutefir,
    se pasa a usar el cliente python disponible `client.py` y un clon de éste para Brutefir `brutefir_cli.py`.
    
- Se observa un error en la aritmética del loudness y tonos en `server_process.py`:

    IndexError: only integers, slices (`:`), ellipsis (`...`), numpy.newaxis (`None`) and integer or boolean arrays are valid indices
    
    La versión anterior de Python generaba un mensaje que advertía de esta posibilidad en un futuro, que ya ha llegado. El motivo es que las variables loudness_i, bass_i y treble_i resultan ser float y falla su uso para hacer slices en el array de loudness o tonos. Quedan convertidas a integer.

- Algunas correcciones en los archivos de ejemplo `audio/config`, `audio/status` y `presets.ini`

- Instalación incondicional de `python-scipy`, `python-matplotlib` y `python-mpd` (se indica en la wiki).

- Scripts actualizados:

    `bin/initfirtro.py` `bin/presets.py` `bin/read_brutefir_process.py` `bin/server_process.py`

## 2017- agosto. Cambios

- Se hace opcional el pausado de reproductores (MPD, Mplayer, Mopidy) si no son la entrada activa para ahorro de %CPU.

- Se implementa un mecanismo opcional que vincula el volumen de FIRtro con el de MPD.


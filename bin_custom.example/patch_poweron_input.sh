#!/bin/bash

# Se pretende evitar que FIRtro arranque con una input no deseada.
# Por ejemplo mi input 'apple_tv' es digital y si está apagado
# notaremos ruido blanco intermitente al arrancar
# Entonces podemos alterar la input de audio/status antes de
# arrancar FIRtro, insertando una llamada a este script en /etc/rc.local

# ---- CONFIGURACION ----
#badInput=apple  # pattern
badInput=spoti  # pattern
goodInput=pulse

# ---- MAIN ----

#statusfile="/home/firtro/audio/status"
statusfile="tmp/status"

if [[ ! $(grep -i $badInput $statusfile) == '' ]]; then
    # insert la nueva linea, para append seria '/pattern/a nueva_linea '
    sed -i '/input\ =/i input\ =\ '$goodInput  $statusfile
    # borramos la vieja '/pattern/d'
    sed -i '/'$badInput'/d'  $statusfile
fi

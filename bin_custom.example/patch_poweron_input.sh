#!/bin/bash

# Se pretende evitar que FIRtro arranque con una input no deseada.
# Por ejemplo mi input 'apple_tv' es digital y si está apagado
# notaremos ruido blanco intermitente al arrancar, 
# ya que el resampler hacia Jack no sincroniza.
#
# Entonces podemos alterar la input de audio/status antes de
# arrancar FIRtro, insertando una llamada a este script en /etc/rc.local
# antes de la ejecución de initfirtro.py

# Ejemplo de uso:
# rc.local
#   su -l firtro -c 'patch_poweron_input.sh   apple  pulse'

# ---- CONFIGURACION ----
badInput=$1
newInput=$2

# ---- MAIN ----
statusfile='/home/firtro/audio/status'
if [[ ! $(grep -i $badInput $statusfile) == '' ]]; then
    # insert la nueva linea, para append seria '/pattern/a nueva_linea '
    sed -i '/input\ =/i input\ =\ '$newInput  $statusfile
    # borramos la vieja '/pattern/d'
    sed -i '/'$badInput'/d'  $statusfile
fi

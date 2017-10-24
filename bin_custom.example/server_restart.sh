#!/bin/bash

# matamos el server del FIRtro
pkill -f "python /home/firtro/bin/server.py"

# OjO hay veces que se queda algún proceso escuchando en 9999/tcp,
# por ejemplo alsa_in ¿!?, hay que matarlo para liberar el puerto:
echo "liberando el puerto 9999 ... .. ."
fuser -kv 9999/tcp

# rearrancamos el server del FIRtro (9999/tcp)
/home/firtro/bin/server.py &


#!/bin/bash

verEstado () {
grep "level ="  /home/firtro/audio/status
grep "input ="  /home/firtro/audio/status
grep "mono ="   /home/firtro/audio/status
jack_conexiones.py ">"
}

echo " --- estado inicial:"
verEstado
echo ""

echo "--- cambio a estereo:"
control mono off
sleep 2
verEstado

echo "--- cambio a mono:"
control mono on
sleep 2
verEstado

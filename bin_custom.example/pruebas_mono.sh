#!/bin/bash

loadEcasound=$(grep load_ecasound /home/firtro/audio/config | cut -d"=" -f2)
if [ $loadEcasound == True ]; then
    pfirtro="ecasound"
else
    pfirtro="brutefir"
fi

verEstado () {
echo "attBfir =" $(ba|tail -n1)
grep "level ="  /home/firtro/audio/status
grep "input ="  /home/firtro/audio/status
grep "mono ="   /home/firtro/audio/status
jack_conexiones.py ">" | grep " "$pfirtro | sort
}

echo " --- estado inicial:"
verEstado
echo ""

echo "--- cambio a estereo:"
control mono off
sleep 2
verEstado
echo ""

echo "--- cambio a mono:"
control mono on
sleep 2
verEstado
echo ""

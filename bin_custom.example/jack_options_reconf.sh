#!/bin/bash
# v1.0

if [ ! $1 ]; then
    echo ""
    echo "    Script para ayudar a reconfigurar las opciones de jack en audio/config"
    echo "    Ejemplo de uso:  jack_options_reconf.sh  -p1024 -n3 -S"
    echo "    Nota:            omitir '-d device' y '-r rate'"
    echo ""
    exit 0
fi

f=/home/firtro/audio/config
viejaLinea=$(grep "^jack_options" $f)
echo ""
echo "actual: "$viejaLinea
echo ""


read -r -p "ATENCION: deseas continuar? [y/N] " tmp
if [ "$tmp" != "y" ] && [ "$tmp" != "Y" ]; then
    echo Bye.
    exit 0
fi

# Leemos las opciones
opciones=""
for x in "$@"; do
    opciones+=$x" "
done
nuevaLinea="jack_options = -R -dalsa "$opciones

# 'c' es el comando de 'sed' que reemplaza lineas completas de un archivo 
# que matchean con /loquetiendelante/, entonces las reemplaza con loquetienedetrás.
sed -i -e "/^jack_options*/c$nuevaLinea"   $f

echo ""
echo "nuevo:  "$(grep "^jack_options" $f)
echo ""

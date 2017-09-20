#!/bin/bash

if [ -z $1 ] ; then
    echo uso indicando la branch:
    echo "    bajaFIRtro.sh  master | testing | xxxx"
    echo
    exit 0
fi
branch=$1

# Prepara el directorio temporal /home/firtro/tmp/
mkdir /home/firtro/tmp > /dev/null 2>&1
cd /home/firtro/tmp
# Borra si existiera algun zip o directorio de la branch solicitada
rm $branch.zip
rm -r FIRtro-$branch
# Baja el zip de la branch
wget https://github.com/AudioHumLab/FIRtro/archive/$branch.zip
# Se descomprime en su directorio y se borra el zip recien bajado.
unzip $branch.zip
rm $branch.zip

# Se copian los scripts de instalación en /home/firtro/tmp para facilitar su ejecucion
cp -f FIRtro-$branch/.install/*sh .
# Se regresa al home
cd

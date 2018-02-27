#!/bin/bash

version="0.1"
#
# Cutre script para guardar los archivos importantes de FIRtro
# Los archivos y directorios a guardar deben estar definidos en
#                        saveFIRtro.cfg

###  CONFIGURAR AQUI EL DIRECTORIO DE DESTINO:
#    (normalmente será un medio externo que previamente habremos montado)
basedir="/mnt/qnas/FIRtros_BUs/"
###


# Crea el directorio base de copias de esta máquina en el destino
basedir+=$HOSTNAME"/"
timestamp=$(date +%Y%m%d-%H%M)
echo ""
if   [[ $1 == *"-d"* ]]; then
    basedir+=$timestamp"/"
    echo "Destino: "$basedir
    echo ""
elif [[ $1 == *"-n"* ]]; then
    echo "Destino: "$basedir
    echo""
else
    echo "versión "$version
    echo ""
    echo "Uso: saveFIRtro.sh  --dated | --nodated"
    echo ""
    echo "     La lista de archivos/directorios a copiar"
    echo "     se leerá desde el archivo saveFIRtro.cfg"
    echo ""
    exit 0
fi

if ! mkdir -p $basedir ; then
    echo ""
    echo "¿Está montado el directorio de destino?"
    echo ""
    exit 0
fi

# Lee la lista de archivos y/o carpetas origen
# que se encuentra en el archivo emparejado 'saveFIRtro.cfg'
myfname=$0
flista="${myfname/sh/cfg}"
lista=( $(cat $flista) )

# Hace la copia
for cosa in ${lista[@]}; do
    # Eludimos posibles comentarios
    if [[ $cosa != *"#"* ]] && [[ $cosa != *";"* ]]; then
        echo "copiando "$cosa" ..."
        cp -r --parents $cosa $basedir
    fi
done
echo ""
echo "Done."
echo ""

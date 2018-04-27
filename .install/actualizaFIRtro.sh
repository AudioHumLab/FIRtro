#!/bin/bash

# v1.0b
#   Dejamos un archivo indicando la branch actualizada

# NOTAS previas:
#
# - Las carpetas *custom*/ y lspk/ no se modifican,
#   excepto algunos archivos propios de la distro:
#       altavoces de ejemplo en lspk/
#       y algunas utilidades en bin_custom.example/
#
# - La carpeta music/ se proporciona con una pista de ejemplo
#   para poder probar la BD de MPD
#
# - Los archivos de configuración se proporcionan con extensión .example
#       audio/status.example
#       audio/inputs.example
#       audio/config.example
#       www/config/config.ini.example
#   Se renombrarán sin la extensión si se decide no conservar las configuraciones

# VERIFICAMOS OPCIONES
# si no se pasa argumento con la branch
if [ -z $1 ] ; then
    echo uso indicando la branch xxx disponible en ~/tmp/FIRtro-xxx:
    echo "    bajaFIRtro.sh master|testing|xxx"
    echo
    exit 0
fi

destino=/home/firtro
branch=$1
origen=$destino/tmp/FIRtro-$branch

# Si no se localiza la branch indicada
if [ ! -d $origen ]; then
    echo
    echo ERROR: no se localiza $origen
    echo uso indicando la branch xxx disponible en ~/tmp/FIRtro-xxx:
    echo "    bajaFIRtro.sh master|testing|xxx"
    echo
    exit 0
fi

# Preguntamos si se quieren conservar las configuraciones actuales
conservar="1"
read -r -p "ATENCION: deseas conservar las configuraciones actuales? [Y/n] " tmp
if [ "$tmp" = "n" ] || [ "$tmp" = "N" ]; then
    echo Se sobreescribiran todos los archivos.
    read -r -p "Estás seguro segurísimo? [y/N] " tmp
    if [ "$tmp" = "y" ] || [ "$tmp" = "Y" ]; then
        conservar=""
    else
        conservar="1"
        echo Se conservarán las configuraciones actuales.
    fi
fi

read -r -p "ATENCION: deseas continuar con la actualización? [y/N] " tmp
if [ "$tmp" != "y" ] && [ "$tmp" != "Y" ]; then
    echo Bye.
    exit 0
fi


################################################################################
###                                 INICIO                                   ###
################################################################################

cd $destino

######################################################################
# Preventivo: hacemos respaldos .LAST de lo que hubiera ya configurado
######################################################################
echo "(i) Guardando respaldos *.LAST de archivos de configuración"

## carpeta RAIZ:
cp .mpdconf                 .mpdconf.LAST
cp .brutefir_defaults       .brutefir_defaults.LAST
## carpeta MPLAYER
cp .mplayer/config          .mplayer/config.LAST
cp .mplayer/channels.conf   .mplayer/channels.conf.LAST

## carpeta AUDIO:
cp audio/status             audio/status.LAST
cp audio/inputs             audio/inputs.LAST
cp audio/config             audio/config.LAST
cp audio/radio              audio/radio.LAST
cp audio/cards.ini          audio/cards.ini.LAST
cp audio/config_mcd         audio/config_mcd.LAST
cp audio/config_media       audio/config_media.LAST
rm -f audio/asound*LAST     # por si hubiera anteriores no los replicamos
for file in audio/asound* ; do
    mv "$file" "$file.LAST"
done
rm -f audio/PEQx*LAST       # por si hubiera anteriores no los replicamos
for file in audio/PEQx* ; do
    mv "$file" "$file.LAST"
done

## carpeta WWW:
cp www/config/config.ini    tmp/www_config.ini.LAST # en tmp/ pq www/ desaparecerá

## carpeta BIN/ (scripts de los BOTONES CUSTOM de la WEB):
if ls bin/webcustombutton* >/dev/null 2>&1; then
    cp bin/webcustombutton* tmp/
fi

#########################################################
# Limpieza
#########################################################
echo "(i) Borrando archivos antiguos de FIRtro"
rm -f CHANGES*
rm -f LICENSE*
rm -f README*
rm -f WIP*
rm -rf bin/ # -f porque pueden haber *.pyc protegidos
rm -r doc/
rm -r www/
rm .brutefir_c*

#########################################################
# Copiamos lo nuevo
#########################################################
echo "(i) Copiando archivos nuevos desde $origen en $destino"
cp -r $origen/*             $destino/
# y los ocultos se deben explicitar para que se copien:
cp $origen/.mpdconf         $destino/
cp $origen/.brutefir*       $destino/
cp -r $origen/.mplayer*     $destino/

########################################################################
# Si se ha pedido conservar las configuraciones las restauramos:
########################################################################
if [ "$conservar" ]; then
    echo "(i) Restaurando configuraciones de usuario"

    # carpeta RAIZ:
    echo "    ".mpdconf
    mv .mpdconf.LAST                .mpdconf
    echo "    .brutefir_defaults"
    mv .brutefir_defaults.LAST      .brutefir_defaults

    # carpeta MPLAYER
    echo "    ".mplayer/config
    mv .mplayer/config.LAST         .mplayer/config
    echo "    ".mplayer/channels.conf
    mv .mplayer/channels.conf.LAST  .mplayer/channels.conf

    # carpeta WWW
    echo "    "www/config/config.ini
    cp tmp/www_config.ini.LAST      www/config/config.ini

    # carpeta AUDIO:
    for file in audio/*LAST ; do
        nfile=${file%.LAST}         # elimina .LAST encontrado al final '%'
        echo "    "$nfile
        mv $file $nfile
    done

########################################################################
# Si NO se ha pedido conservar las configuraciones, se sobreescriben:
########################################################################
else
    # Algunos archivos de configuracion se proporcionan con extension .example:
    cp audio/status.example             audio/status
    cp audio/config.example             audio/config
    cp audio/inputs.example             audio/inputs
    cp www/config/config.ini.example    www/config/config.ini
fi

# Caso especial que se ha tratado en tmp/ lo quitamos de ahí
mv -f tmp/www_config.ini.LAST    www/config/config.ini.LAST

########################################################################
## carpeta BIN: scripts previos de los BOTONES CUSTOM de la WEB
########################################################################
if ls tmp/webcustombutton* >/dev/null 2>&1; then
    mv -f tmp/webcustombutton* bin/
fi

#########################################################
# restaurando FIFOS
#########################################################
echo "(i) Creando fifos para mplayer"
rm -f *fifo
mkfifo tdt_fifo
mkfifo cdda_fifo

#########################################################
# restaurando brutefir_convolver
#########################################################
echo "(i) Un primer arranque de Brutefir para que genere archivos internos"
brutefir

#########################################################
# restaurando permisos
#########################################################
chmod +x bin/*
chmod +x bin_custom/*
chmod +x bin_custom.example/*
chmod -R 755 www/*
chmod 666 www/config/config*
cd

#########################################################
# FIN
#########################################################
# Dejamos una marca indicando la branch contenida
echo "as per actualizaFIRtro.sh" > "~/bin/aa_README_THIS_IS_"$branch"_BRANCH"
echo ""
echo "(i) Hecho. Para probar la configuración de prueba de FIRtro ejecutar el comando:"
echo "    initfirtro.py"
echo ""


#########################################################
# Website 'FIRtro'
#########################################################
forig=$origen"/.install/FIRtro.conf"
fdest="/etc/apache2/sites-available/FIRtro.conf"
actualizar=1
echo ""
echo "(i) Comprobando el website 'FIRtro'"
echo "    /etc/apache2/sites-available/FIRtro.conf"
echo ""

if [ -f $fdest ]; then
    if ! cmp --quiet $forig $fdest; then
        echo "(i) Se dispone de una nueva version en "
        echo "    "$forig"\n"
    else
        echo "(i) No ha cambios en el website\n"
        actualizar=""
    fi
fi
if [ "$actualizar" ]; then
    echo "Atencion se necesitan permisos de administrador (sudo).\n"
    sudo cp $forig $fdest
    sudo a2ensite FIRtro.conf
    sudo a2dissite 000-default.conf
    sudo service apache2 reload
fi


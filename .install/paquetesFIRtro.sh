#!/bin/bash

# v0.1
# v0.2 se incluye la instalacion de py-jack

echo ""
echo "(i) para instalar los paquetes debes ser"
echo "    un usuario autorizado (sudoer)"
read -p "    - pulsa intro -" dummy
echo ""

read -r -p "ATENCION: deseas continuar? [y/N] " tmp
if [ "$tmp" != "y" ] && [ "$tmp" != "Y" ]; then
    echo Bye.
    exit 0
fi

echo "(i) Actualizamos las BD de paquetes"
sudo apt-get update

# Paquetes de software de utilidad general
sudo apt-get install htop mc unzip rsync ipython # usbmount


# 4.0 ALSA
sudo apt-get install alsa-utils
if ! grep "snd_dummy" /etc/modules >/dev/null 2>&1; then
    echo snd_dummy >> /etc/modules
fi

# 4.2 Python 2.7
sudo apt-get install python-numpy python-scipy python-matplotlib python-mpd

# 4.3 Jack (OJO asumimos JACK2)
sudo apt-get install jackd2
sudo adduser firtro audio

# Jack, ajuste policy en d-bus para que 'firtro' tenga acceso a los Device de Audio:
fconfig=/etc/dbus-1/system-local.conf
#  Variable auxiliar para crear un fichero de configuracion de dbus
newcontent="<busconfig>\n\n \
 <!-- FIRtro -->\n \
 <policy user=\"firtro\">\n \
   <allow own=\"org.freedesktop.ReserveDevice1.Audio0\"/>\n \
   <allow own=\"org.freedesktop.ReserveDevice1.Audio1\"/>\n \
   <allow own=\"org.freedesktop.ReserveDevice1.Audio2\"/>\n \
   <allow own=\"org.freedesktop.ReserveDevice1.Audio3\"/>\n \
 </policy>\n \
\n</busconfig>"
#  Para la edicion de un fichero existente con sed hay que escapar las barras,
#  entonces usamos otra variable auxiliar:
toadd="\n  <!-- FIRtro -->\n \
 <policy user=\"firtro\">\n \
   <allow own=\"org.freedesktop.ReserveDevice1.Audio0\"\/>\n \
   <allow own=\"org.freedesktop.ReserveDevice1.Audio1\"\/>\n \
   <allow own=\"org.freedesktop.ReserveDevice1.Audio2\"\/>\n \
   <allow own=\"org.freedesktop.ReserveDevice1.Audio3\"\/>\n \
 <\/policy>\n \
\n<\/busconfig>"
# Si ya exitiera el fichero de configuracion dbus, lo editamos:
if [ -f $fconfig ]; then
    sudo sed -i -e "s/<\/busconfig>/$toadd/" $fconfig
# pero si no existe lo creamos:
else
    # el 'echo' directo no funciona, usamos un paso intermedio:
    echo $newcontent > $HOME"/tmp/system-local.conf"
    sudo cp $HOME"/tmp/system-local.conf" $fconfig
    rm $HOME"/tmp/system-local.conf"
fi
# reinicio del servicio DBUS
sudo service dbus restart

# 4.4 Brutefir
sudo apt-get install brutefir
# Nota el ajuste de swapoff se gestiona en otro script de instalacion

# 4.5 Ecasound
sudo apt-get install ecasound ecatools python-ecasound ladspa-sdk fil-plugins

# 4.7 Otro software
# SoX
sudo apt-get install sox libsox-dev libsoxr-dev libsoxr-lsr0
# source-highlight
sudo apt-get install source-highlight
# librería para ALSA
sudo apt-get install libasound2-dev
# Librerias para JACK (!) OJO asumimos JACK2
sudo apt-get install libjack-jackd2-dev
# Librerias para Python y para compilar
sudo apt-get install python-dev gcc flex

# Modulo py-jack para comunicar con Jack desde Python (no es paquete Debian)
# OPC 1:
# primero instala 'pip' y se auto-actualiza ('pip' es la utilidad de paquetes python)
sudo apt-get install python-pip
sudo pip install --upgrade python-pip
# y ahora instala 'py-jack'
sudo pip install py-jack
# OPC 2: (se usa la 1)
#cd /tmp
#wget https://netix.dl.sourceforge.net/project/py-jack/py-jack/0.5.2/pyjack-0.5.2.tar.gz
#tar -xf pyjack-0.5.2.tar.gz
#cd pyjack-0.5.2
#sudo sh install.sh
#sudo rm -rf /tmp/pyjack-0.5.2*
#cd

# 6. Servidor de la página web
sudo apt-get install apache2 libapache2-mod-php
# Nota: la activacion del site web se gestiona en otro script.

# 7.1 Servidor de música MPD (Music Player Daemon)
sudo apt-get install mpd mpc
# Servicios SystemV
sudo service  mpd stop
sudo update-rc.d mpd remove
# Servicios Systemd
sudo systemctl stop mpd.service
sudo systemctl disable mpd.service
sudo systemctl stop mpd.socket
sudo systemctl disable mpd.socket

# 7.2 El reproductor multimedia Mplayer
sudo apt-get install mplayer

# limpieza
echo "Limpieza de paquetes con apt autoremove:"
sudo apt autoremove


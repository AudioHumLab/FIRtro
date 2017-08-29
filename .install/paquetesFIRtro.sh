#!/bin/bash

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

# Actualizamos las BD de paquetes
sudo apt-get update

# 3 Paquetes de software de utilidad general
sudo apt-get install htop mc unzip rsync ipython # usbmount


# 4.0 ALSA
if ! grep "snd_dummy" /etc/modules >/dev/null 2>&1; then
    echo snd_dummy >> /etc/modules
fi

# 4.2 Python 2.7
sudo apt-get install python-numpy python-scipy python-matplotlib python-mpd

# 4.3 Jack (OJO asumimos JACK2)
sudo apt-get install jackd2
sudo adduser firtro audio

# 4.4 Brutefir
sudo apt-get install brutefir
# !!!  OjO AQUI FALTARIA INSERTAR swappoff -a antes del exit 0 en /etc/rc.local

# 4.5 Ecasound
sudo apt-get install ecasound ecatools python-ecasound ladspa-sdk fil-plugins

# 4.7 Otro software
sudo apt-get install sox libsox-dev libsoxr-dev libsoxr-lsr0
sudo apt-get install source-highlight
sudo apt-get install libasound2-dev
# !!! OJO asumimos JACK2
sudo apt-get install libjack-jackd2-dev
sudo apt-get install python-dev gcc flex

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

# grupos para el usuario firtro
sudo usermod -a -G cdrom,audio,video,plugdev firtro


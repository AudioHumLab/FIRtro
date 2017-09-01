#!/bin/bash

# ADHESION A GRUPOS (OJO necesitaria firtro en sudo, se traslada a paquetesFIRtro.sh)
# sudo usermod -a -G cdrom,audio,video,plugdev firtro

# ALGUNAS VARIABLES DE ENTORNO

f=/home/firtro/.bashrc

if ! grep "bin_custom" $f >/dev/null 2>&1; then
    echo ""
    echo export PATH=\$HOME/bin_custom:\$HOME/bin:\$PATH >> $f
fi

if ! grep "src-hilite-lesspipe" $f >/dev/null 2>&1; then
    echo "" >> $f
    echo "# resaltado en color de codigo fuente con less" >> $f
    echo "# less source highlighting" >> $f
    echo "export LESSOPEN='| /usr/share/source-highlight/src-hilite-lesspipe.sh %s'" >> $f
    echo "export LESS=' -R '" >> $f
fi
if ! grep "PYTHONDONTWRITEBYTECODE=1" $f >/dev/null 2>&1; then
    echo "" >> $f
    echo "# esto evita la aparicion de archivos .pyc .pyo" >> $f
    echo "export PYTHONDONTWRITEBYTECODE=1" >> $f
fi

# Ajustes para el editor de archivos de texto nano
f=/home/firtro/.nanorc
if ! grep "set tabsize 4" $f >/dev/null 2>&1; then
    echo "" >> $f
    echo "set tabsize 4"    >> $f
fi
if ! grep "set tabstospaces" $f >/dev/null 2>&1; then
    echo "" >> $f
    echo "set tabstospaces" >> $f
fi

# Ajustes DBUS para jackd2
if ! grep "DBUS_SESSION_BUS_ADDRESS" /home/firtro/.profile >/dev/null 2>&1; then
    echo "export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/dbus/system_bus_socket" >> /home/firtro/.profile
fi

# CARPETA PARA MPD
mkdir -p /home/firtro/.config/mpd/playlists
mkdir -p /home/firtro/music

# CARPETA PARA MPLAYER
mkdir -p /home/firtro/.mplayer

# CARPETA TEMPORAL
mkdir -p /home/firtro/tmp

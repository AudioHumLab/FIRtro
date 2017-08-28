#!/bin/bash

# Grupos (OJO necesitaria firtro en sudo, se traslada a paquetesFIRtro.sh)
# sudo usermod -a -G cdrom,audio,video,plugdev firtro

# algunas variables de entorno

f=/home/firtro/.bashrc
if ! grep "src-hilite-lesspipe" $f >/dev/null 2>&1; then
    echo "" >> $f
    echo "# resaltado en color de codigo fuente con less" >> $f
    echo "# less source highlighting" >> $f
    echo "export LESSOPEN='| /usr/share/source-highlight/src-hilite-lesspipe.sh %s'" >> $f
    echo "export LESS=' -R '" >> $f
fi
if ! grep "PYTHONDONTWRITEBYTECODE=1" $f >/dev/null 2>&1; then
    echo "" >> $f
    echo "# esto evita la aparicion de archivos .pyc .pyo" >> /home/firtro/.bashrc
    echo "export PYTHONDONTWRITEBYTECODE=1" >> /home/firtro/.bashrc
fi

f=/home/firtro/.nanorc
if ! grep "set tabsize 4" $f >/dev/null 2>&1; then
    echo "" >> $f
    echo "set tabsize 4"    >> $f
fi
if ! grep "set tabstospaces" $f >/dev/null 2>&1; then
    echo "" >> $f
    echo "set tabstospaces" >> $f
fi

# carpeta para mpd
mkdir -p /home/firtro/.config/mpd/playlists
mkdir -p /home/firtro/music

# carpeta para mplayer
mkdir -p /home/firtro/.mplayer

# carpeta temporal
mkdir -p /home/firtro/tmp

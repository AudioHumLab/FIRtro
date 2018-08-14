#!/bin/bash

# Cutrescript para relanzar FIRtro con otro altavoz

# v0.3
#  - Matamos el server para que no interfiera
#  - Comprueba posible initfirtro.py en curso

# 00. Esperamos hasta 30 seg a que acabe un posible initfirtro.py en curso
i=30
while true; do
    if [ $(pgrep -f initfirtro.py) ]; then
        echo "(lspk_change) Esperando fin de 'initfirtro.py' en curso ..."
        sleep 1
    else
        break
    fi
    i=$(( i-1 ))
    if [ $i -eq 0 ]; then
        echo "(lspk_change) WARNING initfirtro.py no ha finalizado"
        exit 0
    fi
done

# 0. Comprobammos que disponemos de la carpeta de configuración del altavoz
altavoz=$1
if [ ! $altavoz ]; then
    echo "indicar altavoz"
    exit 0
fi
if [ -d /home/firtro/lspk/$altavoz ]; then
    echo "(lspk_change) Se reiniciará FIRtro con el altavoz: "$altavoz
else
    echo "NO existe "$altavoz
    exit 0
fi

# 1. Matamos el server para que no interfiera:
echo "(lspk_change) Cerrando server.py"
pkill -f "python /home/firtro/bin/server.py"
# OjO hay veces que se queda algún proceso escuchando en 9999/tcp,
# por ejemplo alsa_in ¿!?, hay que matarlo para liberar el puerto:
fuser -kv 9999/tcp

# nota: para reemplazar en un archivo una linea que cumpla una pattern con otra linea:
# sed -e '/pattern_de_linea_a_reeemplazar/c\nueva_linea'   /path/to/file

# 2. Configuramos el altavoz solicitado en audio/config
sed  -i.bak -e '/loudspeaker\ \=/c\loudspeaker\ \=\ '$altavoz /home/firtro/audio/config
echo "(lspk_change) audio/config  ---> "$(grep ^loudspeaker /home/firtro/audio/config)

# 3. Si hay algún preset previsto en la carpeta del altavoz,
#    lo cargamos en audio/status para que se use en el arranque:
tmp=$(grep "\[" /home/firtro/lspk/$altavoz/presets.ini \
      | grep -v ";" | grep -v "#" | sed 's/\[//g' | sed 's/\]//g')
preset=$(echo $tmp | cut -d" " -f1)
if [ $preset ]; then
    sed  -i -e '/preset/c\preset\ \=\ '$preset /home/firtro/audio/status
else
    # Si no lo hubiera, borramos el preset de audio/status:
    sed  -i -e '/preset/c\preset\ \=\ ' /home/firtro/audio/status
fi
echo "(lspk_change) audio/status  ---> "$(grep preset /home/firtro/audio/status)

# 4. Reiniciamos los módulos de audio de FIRtro
echo "(lspk_change) REINICIANDO los módulos de audio de FIRtro:"
/home/firtro/bin/initfirtro.py audio

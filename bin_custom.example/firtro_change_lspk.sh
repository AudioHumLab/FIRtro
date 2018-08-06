#!/bin/bash

# Cutrescript para relanzar FIRtro con otro altavoz

# 1. Comprobammos que disponemos de la carpeta de configuración del altavoz
altavoz=$1
if [ ! $altavoz ]; then
    echo "indicar altavoz"
    exit 0
fi
if [ -d /home/firtro/lspk/$altavoz ]; then
    echo "(i) Se reiniciará FIRtro con altavoz '"$altavoz"' ... ..."
else
    echo "NO existe "$altavoz
    exit 0
fi

# Para reemplazar una linea que cumpla una pattern con otra linea:
# sed -e ‘/pattern_de_linea_a_reeemplazar/c\nueva_linea’   /path/to/file

# 2. Si hay algún preset previsto en la carpeta del altavoz,
#    lo cargamos en audio/status para que se use en al arranque:
tmp=$(grep "\[" /home/firtro/lspk/$altavoz/presets.ini \
      | grep -v ";" | grep -v "#" | sed 's/\[//g' | sed 's/\]//g')
preset=$(echo $tmp | cut -d" " -f1)
if [ $preset ]; then
    echo "(i) Configurando preset '"$preset"' en audio/status"
    sed  -i.bak -e '/preset/c\preset\ \=\ '$preset /home/firtro/audio/status
else
    # Si no lo hubiera, borramos el preset de audio/status:
    echo "(i) Borrando preset de audio/status"
    sed  -i.bak -e '/preset/c\preset\ \=\ ' /home/firtro/audio/status
fi

# 3. Configuramos el altavoz solicitado en audio/config
sed  -i.bak -e '/loudspeaker\ \=/c\loudspeaker\ \=\ '$altavoz /home/firtro/audio/config

# 4. Reiniciamos FIRtro
echo "(i) REINICIANDO FIRtro:"
initfirtro.py

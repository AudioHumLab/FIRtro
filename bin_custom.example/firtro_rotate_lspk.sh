#!/bin/bash

# Cutrescript para relanzar FIRtro rotando
# cada uno de los altavoces disponibles en ~/lspk
# Util para ser asociado a un botón de la web de control.

# 1. Array con la colección de altavoces disponibles:
declare -a altavoces
for tmp in /home/firtro/lspk/* ; do
    altavoz=$(basename $tmp)
    if [[ $altavoz != "ejemplo"* ]]; then
        altavoces=("${altavoces[@]}" "$altavoz")
    fi
done

# 2. Altavoz actual:
curr=$(grep loudspeaker /home/firtro/audio/config | cut -d"=" -f2) echo "(rotate_lspk) Altavoz actual: "$curr

# 3. Recorremos los altavoces y reiniciamos con el siguiente al actual:
marca="false"
for altavoz in "${altavoces[@]}"; do

    # Cambiamos de altavoz
    if [ $marca == "true" ]; then
        echo "(rotate_lspk) Cambiando a:     "$altavoz
        /home/firtro/bin_custom/firtro_change_lspk.sh $altavoz &
        break
    fi

    # Una vez que llegamos al actual, ponemos una marca para el siguiente:
    if [ $altavoz = $curr ]; then # la comparacion necesita un solo corchete :-/
        marca="true"
    fi

done

# ... si hemos llegado aquí es porque estamos usando el último, 
# y se ha acabado el bucle, por tanto cambiamos al primero:
if [ $marca == "true" ]; then
    echo "(rotate_lspk) Cambiando a:     "${altavoces[0]}
    /home/firtro/bin_custom/firtro_change_lspk.sh ${altavoces[0]} &
fi

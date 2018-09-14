#!/bin/bash

# Este script actualiza todos los lspk/xxx/NNNN/brutefir_config con el nuevo
# routing para poder hacer MONO entre las etapas de filtrado 'eq' y 'drc'

# Notas:
# - x1 es lo que se busca, x2 es por lo que se reeamplazará.
# - Las últimas expresiones de abajo contienen /
#   que deben ser escapados \/ para que sed funcione.
# - Buscamos '\ *' cualquier espaciado en la cadena buscada para mejor acierto.

a1='to_filters:\ *"f_drc_L";'
a2='to_filters:   "f_drc_L","f_drc_R";'

b1='to_filters:\ *"f_drc_R";'
b2='to_filters:   "f_drc_L","f_drc_R";'

c1='--- DRC filtering'
c2='--- DRC filtering (se reciben los dos canales para poder hacer MONO)'

d1='from_filters:\ *"f_eq_L";'
d2='from_filters: "f_eq_L"\/\/1,"f_eq_R"\/\/0;'

e1='from_filters:\ *"f_eq_R";'
e2='from_filters: "f_eq_L"\/\/0,"f_eq_R"\/\/1;'

files=$(find /home/firtro/lspk/ -name brutefir_config)

for f in $files; do

    # OjO para asegurar que la sustitución funcione con variables hay que
    # insertarlas entrecomilladas "$a1" interrumpiendo las comillas
    # simples de la propia expresión de sustitución.
    sed --in-place=.bak.mono \
        -e 's/'"$a1"'/'"$a2"'/g' \
        -e 's/'"$b1"'/'"$b2"'/g' \
        -e 's/'"$c1"'/'"$c2"'/g' \
        -e 's/'"$d1"'/'"$d2"'/g' \
        -e 's/'"$e1"'/'"$e2"'/g' \
        $f
    echo $f
done
echo Done.

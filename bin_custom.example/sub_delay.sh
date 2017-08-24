#!/bin/bash

# CUTRE SCRIPT para experimentar con retardos entre las cajas y el sub.
# Se basa en la orden "cod <output> <delay>" del CLI de Brutefir


########################################################################
# OjO hay que usar las outputs adecuadas a nuestra configuracion:      #
#                                                                      #
outL="lo_L"                                                            #
outR="lo_R"                                                            #
#                                                                      #
outSUB="sw_1"                                                          #
#                                                                      #
########################################################################


if [ $1 ]; then
    echo "cod \"$outL\" $1; quit;" | nc localhost 3000
    echo "cod \"$outR\" $1; quit;" | nc localhost 3000
else
    # >>>>    Instrucciones de uso:   <<<<<
    echo "uso: delay_cajas_sub   samples_cajas   samples_sub"
fi

if [ $2 ]; then
    echo "cod \"$outSUB\" $2; quit;" | nc localhost 3000
fi

echo "lo; quit;" | nc localhost 3000
exit 0

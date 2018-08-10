#!/bin/bash

# Cutre utilidad para ver los procesos de FIRtro en un terminal,
# puede ser util para ver la evolución de los rearranques.

function verlosprocesos {
    for proceso in "${procesos[@]}"; do
        tmp=$(pgrep -la $proceso)
        # resaltamos en bold lel proceso
        tmp=${tmp//$proceso/\\e[1m$proceso\\e[0m}
        echo -e "$tmp" >> ~/tmp/firtro_procesos.txt
    done
    echo "" >> ~/tmp/firtro_procesos.txt
}

clear
while true; do

    # Scripts python
    declare -a procesos=(
                        python
                        )
    verlosprocesos

    # Procesos de audio
    declare -a procesos=(
                        jackd brutefir ecasound
                        )
    verlosprocesos

    # Procesos dependientes de jackd
    declare -a procesos=(
                        zita-j2n zita-n2j alsa_in alsa_out jacktrip
                        )
    verlosprocesos

    # Procesos de players
    declare -a procesos=(
                        mpd mplayer shairport mopidy squeezeslave
                        )
    verlosprocesos

    cat ~/tmp/firtro_procesos.txt
    rm  ~/tmp/firtro_procesos.txt
    sleep .5
    clear
done

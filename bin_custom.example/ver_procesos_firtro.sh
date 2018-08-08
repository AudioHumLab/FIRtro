#!/bin/bash

# cutre utilidad para ver los procesos de FIRtro en un terminal

clear

function verlosprocesos {
    for proceso in "${procesos[@]}"; do
        tmp=$(pgrep -la $proceso)
        # resaltamos en bold lel proceso
        tmp=${tmp//$proceso/\\e[1m$proceso\\e[0m}
        echo -e "$tmp"
    done
    echo ""
}

while true; do

    # Array con los nombres de procesos de audio
    declare -a procesos=(
                        jackd brutefir ecasound
                        )

    verlosprocesos

    # Array con los nombres de procesos dependientes de jackd
    declare -a procesos=(
                        zita-j2n zita-n2j
                        alsa_in alsa_out
                        )
    verlosprocesos

    # Array con los nombres de procesos de players
    declare -a procesos=(
                        mpd mplayer shairport mopidy squeezeslave
                        )

    verlosprocesos

    sleep .5
    clear
done

#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
    Modulo interno para conectar las entradas al dsp,
    también las conecta a posibles monitores.
"""

import os
import subprocess as sp
from sys import path as sys_path
import jack
from time import sleep

HOME = os.path.expanduser("~")
sys_path.append(HOME + "/bin")
from getconfig import *

########################################################################
# Módulo adicional para gestionar sound cards adicionales resampleadas en jack
import soundcards as sc

########################################################################
# Puertos de monitores de la señal, al ser opcionales usaremos try más abajo...
ext_monitor_ports = jack_external_monitors.split()
int_monitor_ports = jack_internal_monitors.split()

########################################################################
# Funcion original del FIRtro levemente modificada para
# usar opcionalmente puertos de monitoreo
########################################################################
def change_input(input_name, in_ports, out_ports, resampled="no"):

    # in_ports  es la lista [L,R] de los puertos capture de jack de la input elegida
    # out_ports es la lista de los puertos de la variable firtro_ports
    # que se resuelve en server_process en función de si se usa Ecasound
    # además de Brutefir.

    # Aquí evaluamos si la entrada requiere resampling por estar en una tarjeta adicional
    if resampled <> "no":
        sc.external_card_resync(in_ports, resampled)

    # Si la entrada NO es MPD o MOPIDY, los pausamos
    # para evitar que sigan reproduciendo lo que estuviera en curso.
    try:
        if load_mpd:
            if 'mpd' not in input_name.lower():
                print "(server_input) Pausando MPD."
                os.system("mpc pause > /dev/null 2>&1 &")
            else:
                os.system("mpc play > /dev/null 2>&1 &")
        if load_mopidy:
            if 'mopidy' not in input_name.lower():
                print "(server_input) Pausando MOPIDY."
                os.system("mpc -p 7700 pause > /dev/null 2>&1 &")
            else:
                os.system("mpc -p 7700 play > /dev/null 2>&1 &")
    except:
        pass
        
    ########################################################
    #     cuerpo principal como el original del FIRtro:    #
    try:
        jack.attach("server_input")

        # Desconectamos todos los clientes de la entrada del FIRtro y de los monitores
        sources_L_firtro = jack.get_connections(out_ports[0])
        sources_R_firtro = jack.get_connections(out_ports[1])
        for source in sources_L_firtro: jack.disconnect(source, out_ports[0])
        for source in sources_R_firtro: jack.disconnect(source, out_ports[1])

        try: #los monitores son opcionales
            sources_L_extMon = jack.get_connections(ext_monitor_ports[0])
            sources_R_extMon = jack.get_connections(ext_monitor_ports[1])
            for source in sources_L_extMon: jack.disconnect(source, ext_monitor_ports[0])
            for source in sources_R_extMon: jack.disconnect(source, ext_monitor_ports[1])
            sources_L_intMon = jack.get_connections(int_monitor_ports[0])
            sources_R_intMon = jack.get_connections(int_monitor_ports[1])
            for source in sources_L_intMon: jack.disconnect(source, int_monitor_ports[0])
            for source in sources_R_intMon: jack.disconnect(source, int_monitor_ports[1])
        except:
            pass
            
        # Y conectamos la entrada a al FIRtro y a los monitores
        for i in range(len(in_ports)):
            
            # apaño provisional: los in_ports previstos en audio/inputs:
            # miniStreamer:capture_1   , no coinciden con el puerto zita-a2j:
            # miniStreamer-01:capture_1, hay que apañarlo
            # (el motivo puede ser un solape temporal en la creación de zita
            # en el módulo soundcards ¿...? )
            inp = in_ports[i]
            inp1, inp2 = inp.split(":")
            for jap in jack.get_ports():
                jap1, jap2 = jap.split(":")
                if (inp1 in jap1) and (inp2 in jap2):
                    inp = jap1 + ":" + jap2

            jack.connect(inp, out_ports[i])
            
            try: #los monitores son opcionales
                jack.connect(in_ports[i], ext_monitor_ports[i])
                jack.connect(in_ports[i], int_monitor_ports[i])
            except:
                pass
        jack.detach()

    except:
        
        # Si hay alguna excepción devolvemos boolean False
        jack.detach()
        print "(server_input) He tenido problemas, que lo sepas"
        return False

    # Y si todo ha ido bien, devolvemos el boolean True
    return True

if __name__ == "__main__":
    print __doc__


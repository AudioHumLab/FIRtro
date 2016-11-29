#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
    Modulo interno para conectar las entradas al procesador,
    también las conecta a posibles monitores.
"""
# v2.0:
# - Adaptación a FIRtro 2.0. Se devuelven valores Boolean para indicar
#   el resultado del cambio de entrada a server_process
# - Se suprimen los sleep. (!) OJO si aparece un "error de cambio de input"
#   puede ser debido un escenario de CPU% muy cargada afectando 
#   a las operaciones jack.disconnect/connect. Para debug se usa logging.
#
# v2.1:
# - Parada de mplayer (s/audio/config) cuando no se está escuchando para ahorrar CPU%

from os import path as os_path, remove as os_remove, system as os_system
from sys import path as sys_path
import jack
from time import sleep

HOME = os_path.expanduser("~")
sys_path.append(HOME + "/bin")
from getconfig import *

# Para recargar el canal de TDT
import radio_channel_byName as radio_byName

# Para leer el status en dinámico
from basepaths import status_filename
from ConfigParser import ConfigParser
st = ConfigParser()
def read_status():
    global radioch, radio
    st.read("/home/firtro/audio/" + status_filename)
    radioch     = st.get("inputs", "radioch")
    radio       = st.get("inputs", "radio")

# Para el debug de excepciones
# https://julien.danjou.info/blog/2016/python-exceptions-guide
# https://docs.python.org/3/howto/logging.html#logging-basic-tutorial
import logging
logFile = '/home/firtro/tmp/server_input.log'
if os_path.isfile(logFile):
    os_remove(logFile)
logging.basicConfig(filename=logFile, level=logging.ERROR)

# Módulo adicional para gestionar sound cards adicionales resampleadas en jack
import soundcards as sc

# Puertos de monitores de la señal, al ser opcionales usaremos try más abajo...
ext_monitor_ports = jack_external_monitors.split()
int_monitor_ports = jack_internal_monitors.split()

# Alias con temporización experimental para operaciones jack.con/disconnect
tj = 0.1
def jack_connect(p1,p2):
    jack.connect(p1, p2)
    sleep(tj)
def jack_disconnect(p1,p2):
    jack.disconnect(p1, p2)
    sleep(tj)

# Funcion original del FIRtro levemente modificada para
# usar opcionalmente puertos de monitoreo
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
                os_system("mpc pause > /dev/null 2>&1 &")
            else:
                os_system("mpc play > /dev/null 2>&1 &")
    except:
        logging.exception("error en if load_mpd")
    
    try:
        if load_mopidy:
            if 'mopidy' not in input_name.lower():
                print "(server_input) Pausando MOPIDY."
                os_system("mpc -p 7700 pause > /dev/null 2>&1 &")
            else:
                os_system("mpc -p 7700 play > /dev/null 2>&1 &")
    except:
        logging.exception("error en if load_mopidy")
        
    # Si la entrada NO es TDT pausamos MPLAYER para ahorro de CPU%
    if load_mplayer_tdt and pause_mplayer_tdt:
        if 'tdt' not in input_name.lower():
            print "(server_input) Parando  MPLAYER."
            os_system("echo stop > /home/firtro/tdt_fifo")
        else:
            read_status() # leemos el ultimo canal de radio escuchado
            print "(serve_input) Resintonizando TDT: " + radioch
            if not radio_byName.select_channel(radioch):
                print "(serve_input) (i) ERROR resintonizando TDT: " + radioch
                

    ################################################################
    #     cuerpo principal CASI como el original de FIRtro 1.0:    #
    try:
        jack.attach("server_input")

        # Desconectamos todos los clientes de la entrada del FIRtro y de los monitores
        sources_L_firtro = jack.get_connections(out_ports[0])
        sources_R_firtro = jack.get_connections(out_ports[1])
        for source in sources_L_firtro:
            jack_disconnect(source, out_ports[0])
        for source in sources_R_firtro:
            jack_disconnect(source, out_ports[1])

        try: #los monitores son opcionales
            if ext_monitor_ports:
                sources_L_extMon = jack.get_connections(ext_monitor_ports[0])
                sources_R_extMon = jack.get_connections(ext_monitor_ports[1])
                for source in sources_L_extMon: jack_disconnect(source, ext_monitor_ports[0])
                for source in sources_R_extMon: jack_disconnect(source, ext_monitor_ports[1])
                sources_L_intMon = jack.get_connections(int_monitor_ports[0])
                sources_R_intMon = jack.get_connections(int_monitor_ports[1])
                for source in sources_L_intMon: jack_disconnect(source, int_monitor_ports[0])
                for source in sources_R_intMon: jack_disconnect(source, int_monitor_ports[1])
        except:
            logging.exception("error en desconexion de monitores")
            
        # Y conectamos la entrada a al FIRtro y a los monitores
        for i in range(len(in_ports)):
            
            # apaño provisional: los in_ports previstos en audio/inputs:
            # miniStreamer:capture_1   , no coinciden con el puerto zita-a2j:
            # miniStreamer-01:capture_1, hay que apañarlo
            # (el motivo puede ser un solape temporal en la creación de zita
            # en el módulo soundcards ¿...? )
            # NOTA: esto ha dejado de ocurrir al reescribir el modulo soundcards.py
            inp = in_ports[i]
            inp1, inp2 = inp.split(":")
            for jap in jack.get_ports():
                jap1, jap2 = jap.split(":")
                if (inp1 in jap1) and (inp2 in jap2):
                    inp = jap1 + ":" + jap2

            try:
                #jack_connect(in_ports[i], out_ports[i])
                jack_connect(inp, out_ports[i])
            except:
                logging.exception("error conectando " + in_ports[i] + " <> " + out_ports[i])
        
            try: #los monitores son opcionales
                if ext_monitor_ports:
                    jack_connect(in_ports[i], ext_monitor_ports[i])
                if int_monitor_ports:
                    jack_connect(in_ports[i], int_monitor_ports[i])
            except:
                logging.exception("error en conexion de monitores")

        jack.detach()

    except:
        
        # Si hay alguna excepción devolvemos boolean False
        logging.exception("error en cuerpo ppal")
        jack.detach()
        print "(server_input) Problemas (ver ~/tmp/server_input.log)"
        return False

    # Y si todo ha ido bien, devolvemos el boolean True
    return True

if __name__ == "__main__":
    print __doc__


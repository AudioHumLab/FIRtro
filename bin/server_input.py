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
# v2.1b:
# - Revisión del uso de los canales de radio
#
# v2.1c
# - Revisión del pausado opcional de fuentes para ahorro de CPU
# - Rev de comentarios del código
#
# v2.1d
# - Se recupera el uso de getstatus para leer un posible cambio de presintonía
# - Se reordena el código para legibilidad

# módulos genéricos
from os import path as os_path, remove as os_remove
from subprocess import Popen
from sys import path as sys_path
from time import sleep
from ConfigParser import ConfigParser
import jack

# módulos del FIRtro
HOME = os_path.expanduser("~")
sys_path.append(HOME + "/bin")

from getconfig import *
from basepaths import status_filename

# FIRtro2: puertos de monitores de la señal (los convertimos a lista)
ext_monitor_ports = jack_external_monitors.split()
int_monitor_ports = jack_internal_monitors.split()

# FIRtro2: gestiona sound cards adicionales resampleadas en jack
import soundcards as sc

# FIRtro2: para reconectar la radio debido a mplayer -ao jack:mplayer:noconnect
import radio_channel

# Para el DEBUG de excepciones
# https://julien.danjou.info/blog/2016/python-exceptions-guide
# https://docs.python.org/3/howto/logging.html#logging-basic-tutorial
import logging
logFile = '/home/firtro/tmp/server_input.log'
if os_path.isfile(logFile):
    os_remove(logFile)
logging.basicConfig(filename=logFile, level=logging.ERROR)

# Alias con temporización experimental para operaciones jack.con/disconnect
def jack_connect(p1, p2):
    jack.connect(p1, p2)
    #sleep(.1)
def jack_disconnect(p1, p2):
    jack.disconnect(p1, p2)
    #sleep(.2)

# Función auxiliar para pausado opcional de fuentes para ahorro de CPU
def pausas_opcionales(input_name):
    # Pausa opcional de MPD
    if load_mpd and pause_mpd:
        if 'mpd' not in input_name.lower():
            print "(server_input) Pausando MPD."
            Popen("mpc pause > /dev/null 2>&1 &", shell=True)
        else:
            print "(server_input) Reanudando MPD."
            Popen("mpc play > /dev/null 2>&1 &", shell=True)
    # Pausa opcional de MOPIDY
    if load_mopidy and pause_mopidy:
        if 'mopidy' not in input_name.lower():
            print "(server_input) Pausando MOPIDY."
            Popen("mpc -p 7700 pause > /dev/null 2>&1 &", shell=True)
        else:
            print "(server_input) Reanudando MOPIDY."
            Popen("mpc -p 7700 play > /dev/null 2>&1 &", shell=True)
    # Pausa opcional de MPLAYER-TDT
    if load_mplayer_tdt and pause_mplayer_tdt:
        if 'tdt' not in input_name.lower():
            print "(server_input) Parando  MPLAYER."
            Popen("echo stop > " + HOME + "/tdt_fifo", shell=True)
        else:
            # releemos el estado por si se hubiera modificado la presintonia (v2.1b)
            status.readfp(statusfile)
            # recuperamos la presintonia
            print "(serve_input) Resintonizando TDT presintonía: " + radio
            if radio_channel.select_preset(radio):
                print "(serve_input) Resintonizando TDT presintonía: " + radio
            else:
                print "(serve_input) ERROR resintonizando TDT presintonía: " + radio

def desconecta_fuentes_de(out_ports):
    """ Desconectamos todos los clientes de la entrada del FIRtro y de los monitores
    """    
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

# Funcion original de FIRtro1 levemente modificada para los puertos de monitoreo opcionales
def change_input(input_name, in_ports, out_ports, resampled="no"):

    # 'in_ports':   Lista [L,R] de los puertos capture de jack de la input elegida
    # 'out_ports':  Lista de los puertos de la variable 'firtro_ports' que se resuelve
    #               en server_process en función de si se usa Brutefir/Ecasound

    # Aquí evaluamos si la entrada requiere resampling por estar en una tarjeta adicional
    if resampled <> "no":
        sc.external_card_resync(in_ports, resampled)

    # Pausado opcional de fuentes para ahorro de CPU
    pausas_opcionales(input_name)

    ####  cuerpo principal CASI como el original de FIRtro1:
    try:
        jack.attach("tmp")
        
        # primero desconectamos todo lo que hubiera en la entrada del firtro y monitores
        desconecta_fuentes_de(out_ports)

        # Y ahora conectamos la entrada deseada a al FIRtro y a los monitores
        for i in range(len(in_ports)):
            try:
                jack_connect(in_ports[i], out_ports[i])
            except:
                logging.exception("error conectando " + in_ports[i] + " <> " + out_ports[i])

            # Los monitores opcionales
            try:
                if ext_monitor_ports:
                    jack_connect(in_ports[i], ext_monitor_ports[i])
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

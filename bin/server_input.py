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
#   Es posible insertar delays en el alias jack_connect/disconnect de abajo.
#
#
# v2.1c
# - Revisión del pausado opcional de fuentes para ahorro de CPU
# - Rev de comentarios del código
#
# v2.1d
# - Se reordena el código para legibilidad
# - Se deja de intervenir aquí en los players integrados (radio, mpd, etc),
#   se recurre al nuevo módulo players_integrated
# v2.1d2
# - Logging sobre $USER/tmp

# módulos genéricos
import os, sys, getpass
from time import sleep
import jack

# módulos de FIRtro
HOME = os.path.expanduser("~")
sys.path.append(HOME + "/bin")
from getconfig import *

# FIRtro2: puertos de monitores de la señal (los convertimos a lista)
ext_monitor_ports = jack_external_monitors.split()
int_monitor_ports = jack_internal_monitors.split()

# FIRtro2: gestiona sound cards adicionales resampleadas en jack
import soundcards as sc
# FIRtro2: gestiona los players integrados en un módulo separado
import players_integrated as players

# LOGGING para el DEBUG de excepciones
# https://julien.danjou.info/blog/2016/python-exceptions-guide
# https://docs.python.org/3/howto/logging.html#logging-basic-tutorial
import logging
# os.getlogin() con login remoto puede ocurrir "OSError: [Errno 25] Inappropriate ioctl for device",
# también puede fallar al arranque de la máquina por ser non login 
try: 
    usuario = os.getlogin()
except:
    #usuario = 'firtro'
    usuario = getpass.getuser()
logFile = '/home/' + usuario + '/tmp/server_input.log'
if os.path.isfile(logFile):
    os.remove(logFile)
logging.basicConfig(filename=logFile, level=logging.ERROR)

# Alias con retardos experimentales (normalmente no usados) para operaciones jack con/disconnect
def jack_connect(p1, p2):
    jack.connect(p1, p2)
    #sleep(.1)
def jack_disconnect(p1, p2):
    jack.disconnect(p1, p2)
    #sleep(.2)

def desconecta_fuentes_de(out_ports):
    """ Desconectamos todos los clientes de la entrada del FIRtro y de los monitores
    """
    sources_L_firtro = jack.get_connections(out_ports[0])
    sources_R_firtro = jack.get_connections(out_ports[1])
    for source in sources_L_firtro:
        jack_disconnect(source, out_ports[0])
    for source in sources_R_firtro:
        jack_disconnect(source, out_ports[1])

    # Los monitores son opcionales
    try:
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

# Funcion original de FIRtro1 levemente modificada con
# puertos de monitoreo y resincronización de posibles tarjetas externas
def change_input(input_name, in_ports, out_ports, resampled="no"):

    # 'in_ports':   Lista [L,R] de los puertos capture de jack de la fuente elegida
    # 'out_ports':  Lista de los puertos de la variable 'firtro_ports' que se resuelve
    #               en server_process en función de si se usa Brutefir/Ecasound

    # FIRtro2: evaluamos si la entrada requiere resampling por estar en una tarjeta adicional
    if resampled <> "no":
        sc.external_card_resync(in_ports, resampled)

    # CONMUTADOR, como el original de FIRtro1.
    try:
        jack.attach("tmp")

        # Desconectamos todo lo que hubiera en la entrada de FIRtro (y en los posibles monitores):
        desconecta_fuentes_de(out_ports)

        # Posibles PAUSAS opcionales en los PLAYERS INTEGRADOS (ahorro de %CPU):
        players.manage_pauses(input_name)

        # Y ahora conectamos la entrada deseada a FIRtro y a los monitores:
        for i in range(len(in_ports)):
            # Entradas a FIRtro
            try:
                jack_connect(in_ports[i], out_ports[i])
            except:
                logging.exception("error conectando " + in_ports[i] + " <> " + out_ports[i])

            # Los monitores opcionales:
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

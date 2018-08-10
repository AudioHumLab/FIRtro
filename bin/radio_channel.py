#!/usr/bin/python
# -*- coding: utf-8 -*-
# from __future__ import with_statement # This isn't required in Python 2.6

# Notas previas:
# - Las variables 'radio' y 'radio_prev' se refieren a
#   un Id de presintonia de los configurados en audio/radio
# - Este script se usa desde un shell como se hacía en FIRtro1,
#   por tanto, debemos asegurar que la radio funcione con normalidad
#   operando "por fuera del server".
#
# v1.1
# - Adaptacion para ser usado también como módulo importable.
# - Actualizacion de audio/status rotando las presintonias radio y radio_prev
# v1.1b
# - revision, bugs
# v1.1c
# - Comprobamos si el proceso mplayer está accesible

import sys
from subprocess import Popen, check_output
from getstatus import *
from getradio import *
import wait4
from time import sleep

def _update_radio_status(nuevo):
    """ actualiza el archivo de estado de FIRtro rotando los canales de radio actual y previo
    """
    previo = status.get("inputs", "radio")
    if nuevo <> previo:
        status.set('inputs', 'radio_prev', previo)
        status.set('inputs', 'radio', nuevo)
        statusfile = open(status_path, 'w')
        status.write(statusfile)
        statusfile.close()

def select_channel(channel_name):
    """ configura directamente en mplayer un nombre de emisora
    """
    try:
        Popen('echo loadfile dvb://' + "'" + channel_name +"'"+' > ' + tdt_fifo, shell=True)
        return True
    except:
        return False

def select_preset(memo):
    """ selecciona un preset disponible en audio/radio
    """
    # obtenemos el nombre del canal correspondiente a la posicion solicitada
    if memo.isdigit():
        channel_name = channels.get("channels", memo)
        if channel_name <> "":
            # reconfiguramoms mplayer con el canal deseado
            if select_channel(channel_name):
                return True
    return False

if __name__ == "__main__":

    # verificamos que el proceso mplayer para tdt esté accesible:
    if not "tdt_fifo" in check_output("pgrep -fa mplayer", shell=True):
        print "(radio_channel) (!) No se localiza el proceso MPLAYER TDT"
        sys.exit()

    # Lectura de la línea de comandos
    if len(sys.argv) > 1:
        opcion = sys.argv[1]
    else:
        sys.exit()

    # Evaluamos lo que se pide
    if channels.has_option("channels", opcion):
        radio = opcion
    else:
        # Error: salimos.
        print "El canal \"" + opcion + "\" no existe"
        sys.exit()

    # Si se valida lo que se pide, se resintoniza Mplayer:
    if select_preset(radio):
        # Actualizamos los canales en audio/status
        _update_radio_status(radio)
        print "Canal " + radio
        # nota: antes de consultar esperamos un poco a que desaparezca Mplayer
        sleep(3)
        # Si FIRtro está escuchando la TDT le pedimos que restaure la entrada:
        if "tdt" in input_name:
            # Esperamos a que Mplayer vuelva a estar disponible en Jack
            wait4.wait4result("jack_lsp", "mplayer_tdt", quiet=True)
            Popen("control input restore", shell=True)
        # Opcinalmente Mplayer puede printar lo que tiene en curso
        # (solo visible por la consola de initfirtro)
        # Popen("echo get_file_name > tdt_fifo", shell=True)
    else:
        print "El canal \"" + opcion + "\" no está configurado"

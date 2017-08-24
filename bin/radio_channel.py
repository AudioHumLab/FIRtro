#!/usr/bin/python
# -*- coding: utf-8 -*-
# from __future__ import with_statement # This isn't required in Python 2.6

# Notas previas: 
# Las variables 'radio' y 'radio_prev' se refieren a un Id de presintonia de los configurados en audio/radio
# Este script se usaba desde un shell en FIRtro1
#
# v1.1
# - Adaptacion para ser usado también como módulo importable.
# - Actualizacion de audio/status rotando las presintonias radio y radio_prev

import sys
from subprocess import *
from getstatus import *
from getradio import *

# printados de este script si se usa por linea de comandos
def messages():
    print "Canal " + radio

def _update_status(radio):
    """ actualiza el archivo de estado de FIRtro rotando los canales de radio actual y previo
    """
    prev = status.get("inputs", "radio")
    status.set('inputs', 'radio_prev', prev)
    status.set('inputs', 'radio', radio)
    statusfile = open(status_path, 'w')
    status.write(statusfile)
    statusfile.close

# funciones accesibles para uso como módulo importado
def select_channel(channel_name):
    """ configura directamente en mplayer un nombre de emisora
    """
    Popen('echo loadfile dvb://' + "'" + channel_name +"'"+' > ' + tdt_fifo, shell=True)

def select_preset(radio):
    """ selecciona una presintonia disponible en audio/radio
    """
    # obtenemos el nombre del canal correspondiente a la presintonia solicitada
    channel_name = channels.get("channels", radio)
    if channel_name == "":
        print "El canal \"" + opcion + "\" no está configurado"
        return False
        exit()

    # reconfiguramoms mplayer con el canal deseado
    select_channel(channel_name)

    # actualizamos el estado de FIRtro
    _update_status(radio)
    
    return True

if __name__ == "__main__":

    # Lectura de la opcion proporcionada en línea de comandos
    if len(sys.argv) > 1:
        opcion = sys.argv[1]
    else:
        messages()
        exit()

    # (!) pendiente de revisar (no se usa)
    old_input_name = input_name

    # Evaluamos la opcion proporcionada en linea de comandos
    # a) está pendiente aclarar esta opción
    if opcion == "-c":
        pass
    # b) si se pide un Id de presintonia 
    elif channels.has_option("channels", opcion):
        radio = opcion
    # c) opción errónea
    else:
        print "El canal \"" + opcion + "\" no existe"
        exit()

    select_preset(radio)

    # informacion en el terminal
    messages()



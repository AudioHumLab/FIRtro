#!/usr/bin/env python
# -*- coding: utf-8 -*-
# from __future__ import with_statement # This isn't required in Python 2.6
"""
    cliente para dialogar con FIRtro (server.py)
"""

# v1.0b
# se etiquetan los 'print' para identificar la procedencia

import socket
import sys
import os
import json
from getconfig import control_port

def firtro_socket (data, quiet=False):
    server="localhost"
    port=control_port

    s=socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        if not quiet:
            print "(client.py) Connecting to",server, "port",str(port)+"..."
        s.connect((server,port))
    except socket.gaierror, e:
        print "(client.py) Address-related error connecting to server: %s" % e
        sys.exit(-1)
    except socket.error, e:
        print "(client.py) Connection error: %s" % e
        sys.exit(-1)
    if not quiet:
        print "(client.py) Connected"

    try:
        # Si se pasa un parámetro, se envia al servidor y se cierra la conexión
        if data:
            s.send(data)
            recibido = s.recv(4096);
            if data not in ("quit","close"):
                # El server de FIRtro devuelve una cadena json con el estado
                # incluyendo los posibles warnings después de procesar la orden.
                recibido = json.loads(recibido)
                if len(recibido['warnings'])>0:
                    for value in recibido['warnings']:
                        print "(client.py) Warning: " + value
            s.send("close\r\n")

        # Si no se pasa parámetro, se abre una conexión interactiva
        else:
            print "---- client.py - interactive session ----"
            print "---- close: closes the current connection"
            print "---- quit: closes the current connection and the control script"
            while True:
                mensaje=raw_input(">>>")
                s.send(mensaje)
                recibido=s.recv(4096); #print "(client.py)", recibido # DEBUG
                if mensaje=="quit" or mensaje=="close":
                    print "Received data:", recibido
                    break
                else:
                    if not quiet:
                        print "Received data:"
                    recibido = json.loads(recibido)
                    for key, value in recibido.iteritems():
                        print key, value

    except:
        print "(client.py) Unexpected error:", sys.exc_info()[0]

    if not quiet:
        print "(client.py) Closing connection..."

    s.close()
    return recibido

if __name__ == "__main__":

    if len (sys.argv)>1:
        firtro_socket (" ".join(sys.argv[1:]))
    else:
        firtro_socket (None)

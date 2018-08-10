#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
    Cliente para dialogar con FIRtro (server.py)
    Uso:
        client.py [-s servidor] comando [argumentos ...]
"""

# v1.0b
#   Se reescriben algunas líneas para legibilidad, se añaden comentarios.
#   Se etiquetan los 'print' para identificar la procedencia
#   Se añade que la funcion firtro_socket devuelve lo recibido
# v1.0c
#   Se admite especificar el nombre del servidor FIRtro destino, 
#   para poder correr client.py fuera de FIRtro. 

import socket
import sys
import os
import json
from getconfig import control_port

def firtro_socket (data, quiet=False, server="localhost"):
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
                if len(recibido['warnings']) > 0:
                    for value in recibido['warnings']:
                        print "(client.py) Warning: " + value
            s.send("close")

        # Si no se pasa parámetro, se abre una conexión interactiva
        else:
            print "---- client.py - interactive session ----"
            print "---- close: closes the current connection"
            print "---- quit: closes the current connection and the control script"
            while True:
                mensaje = raw_input(">>>")
                s.send(mensaje)
                recibido = s.recv(4096); #print "(client.py)", recibido # para DEBUG
                if mensaje == "quit" or mensaje == "close":
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

    p = sys.argv

    # se puede dar como argumento un server distinto de localhost
    if "-s" in p:
        i = sys.argv.index("-s")
        server = sys.argv[i + 1]
        p.pop(i) # quitamos -s
        p.pop(i) # y el nombre del server
    else:
        server = "localhost"

    firtro_socket (" ".join(p[1:]), server=server)

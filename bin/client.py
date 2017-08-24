#!/usr/bin/env python
# -*- coding: utf-8 -*-
# from __future__ import with_statement # This isn't required in Python 2.6

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
        if not quiet: print "Connecting to",server, "port",str(port)+"..."
        s.connect((server,port))
    except socket.gaierror, e:
        print "Address-related error connecting to server: %s" % e
        sys.exit(-1)
    except socket.error, e:
        print "Connection error: %s" % e
        sys.exit(-1)

    if not quiet: print "Connected"
    try:
        # Si se pasa un parámetro, se envia al servidor y se cierra la conexión
        if data:
            s.send(data)
            recibido=s.recv(4096)
            #print recibido
            if data not in ("quit","close"):
                #print "Received data:"
                recibido = json.loads(recibido)
                #if recibido(warnings): print recibido(warnings)
                if len(recibido['warnings'])>0:
                    for value in recibido['warnings']:
                        print "(client) Warning: " + value
                #for key, value in recibido.iteritems(): print key, value
                s.send("close")
                recibido=s.recv(4096)
        else:
            # Si no se pasa parámetro, se abre una conexión interactiva
            print "close: closes the current connection"
            print "quit: closes the current connection and the control script"
            while True:
                mensaje=raw_input(">>>")
                s.send(mensaje)
                recibido=s.recv(4096)
                #print recibido
                if mensaje=="quit" or mensaje=="close":
                    print "Received data:", recibido
                    break
                else:
                    if not quiet: print "Received data:"
                    recibido = json.loads(recibido)
                    for key, value in recibido.iteritems(): print key, value
    except: print "Unexpected error:", sys.exc_info()[0]
    if not quiet: print "Closing connection..."
    s.close()

if __name__ == "__main__":

    if len (sys.argv)>1:
        firtro_socket (" ".join(sys.argv[1:]))
    else:
        firtro_socket (None)

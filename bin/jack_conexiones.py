#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" 
    Script para printar las conexiones en jack.
    v1.1:
    Admite un literal para filtrar por nombre de puerto
    Admite un símbolo >|< para filtrar por dirección 
    Ejemplo:
    jack_conexiones.py "brutefir" ">"
"""


import jack
from sys import argv as sys_argv, exit as sys_exit

def jackConexiones(nombrePuerto="", direccion="*"):
    """ direccion: > | < | *
        Devuelve una lista de tripletas:
        (puerto, conexion, puerto)
    """
    ports = []
    jack.attach("tmp")
    for puerto in [x for x in jack.get_ports() if nombrePuerto in x]:
        conexiones = jack.get_connections(puerto)
        for conexion in conexiones:
            flags = jack.get_port_flags(conexion)
            # Returns an integer which is the bitwise-or of all flags for a given port.
            # haciendo pruebas veamos algunos flags de puertos:
            # puertos escribibles (playback): 1 21     impares, ultimo bit a 1
            # puertos leibles     (capture) : 2 18 22  pares,   ultimo bit a 0
            if   flags % 2 :
                direc = ">"
            else:
                direc = "<"
            if direc == direccion or direccion == "*":
                ports.append((puerto, " --" + direc + "-- ", conexion))
    jack.detach()
    return ports

if __name__ == "__main__" :
    nombre = ""
    direcc = "*"
    if len(sys_argv) > 1:
        for n in range(1,len(sys_argv)):
            opc = sys_argv[n]
            if opc in ("*", ">", "<"):
                direcc = opc
            elif "-h" in opc:
                print __doc__
                sys_exit(0)
            else:
                nombre = opc
    print
    for x in jackConexiones(nombre, direcc):
        print x[0].ljust(30), x[1], x[2]
    print


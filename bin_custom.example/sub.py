#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
------------OBSOLETO---
este script solo sirve para conectar, desconectar 
o ver la conexión de brutefir hacia las vias de subwoofer (sw*)
"""

import sys, os
from subprocess import check_output
import jack


HOME = os.path.expanduser("~")
sys.path.append(HOME + "/bin")
import jack_conexiones
import lee_brutefir_config as brutefir

def conexionesSW():
    return jack_conexiones.conexiones("sw")

def mapeoSW():
    puertos = []

    for outMap in brutefir.outputs:
        if "sw" in outMap:
            brutefirPort = "brutefir:"+ outMap.split("/")[1].replace('"', '')
            soundCardPort = outMap.split("/")[0].replace('"', '')
            puertos.append((brutefirPort, soundCardPort))

    return puertos

def conectaSW(OnOff):

    for puerto in mapeoSW():
        if OnOff.lower() == "off":
            jack.disconnect(puerto[0], puerto[1])
        else:
            jack.connect(puerto[0], puerto[1])

def muestra_estado():
    
    print
    # si esta conectado mostramos los puertos de brutefir y la conexion:
    if conexionesSW():

        tmp = check_output("echo 'lo;quit;' | nc localhost 3000", shell=True)
        for linea in tmp.split("\n"):
            if "delay" in linea or "Outputs" in linea:
                print linea

        print
        for conex in conexionesSW():
            print conex[0], conex[2], conex[1]

    # si no está conectado informamos:
    else:
        print "desconectado"
            
    print
    
if __name__ == "__main__" :

    # necesario por el cutre diseño del modulo lee_brutefir_config
    brutefir.lee_config()

    accion = ""
    if len(sys.argv) > 1:
        if sys.argv[1].lower() in ["on", "off"]:
            accion = sys.argv[1]
        else:
            print "uso:   sub.py  (on | off) o nada para ver si el SUB está conectado"
            sys.exit()
            
    jack.attach("tmp")
    if accion:
        conectaSW(accion)
    jack.detach()
    
    muestra_estado()

    

#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script custom para restaurar la conexión de la fuente de audio del FIRtro 
hacia los monitores de señal, por ejemplo:

- monitor externo spdif (p.ej el RTA/VU-Meter Behringer Ultracurve 2496)
- monitor (jack) de loudness Ebumeter de Fons Adriaensen
"""
import jack
from sys import path as sys_path
firtroHome = "/home/firtro/"
sys_path.append(firtroHome + "bin/")
from getconfig import *

displays = jack_internal_monitors.split() + jack_external_monitors.split()
if load_ecasound:
    firtro_ports = ecasound_ports
else:
    firtro_ports = brutefir_ports
firtro_ports = firtro_ports.split()  # apaño para las variable cadena de getconfig 


def getDisplaysPorts():
    puertos = jack.get_ports()
    displaysPorts = []

    for display in displays:
        for puerto in puertos:
            if display in puerto:
                displaysPorts.append(puerto)

    return displaysPorts

def desconectaDISPLAYS():
    for portDisplay in getDisplaysPorts():
        clientes = jack.get_connections(portDisplay)
        for cliente in clientes:
            print "(i) desconectando " + cliente + " " + portDisplay
            jack.disconnect(cliente, portDisplay)
    if not getDisplaysPorts():
        print "(?) nada que desconectar"


def conectaDISPLAYS():

    info =[]

    # Primero desconectamos lo que hubiera en los displays, por higiene ;-)
    desconectaDISPLAYS()

    # Tomamos nota de la source:
    source_ports = []
    for p in firtro_ports:
        source_ports += jack.get_connections(p)
    
    # Conectamos los impares:
    for o in source_ports[0::2]:
        for d in getDisplaysPorts()[0::2]:
            info.append("(i) conectando "+ o + " " + d)
            jack.connect(o,d)

    # Conectamos los pares:
    for o in source_ports[1::2]:
        for d in getDisplaysPorts()[1::2]:
            info.append("(i) conectando "+ o + " " + d)
            jack.connect(o,d)

    if info:
        for cosa in info:
            print cosa
    else:
        print "(?) nada que conectar"
        
if __name__ == "__main__":

    try:
        # Nos conectamos al servidor jack bajo el nombre "tmp" por poner algo
        jack.attach("tmp")
        conectaDISPLAYS()
        jack.detach()
    except:
        print "problemas de conexion python a JACK, que lo sepas"







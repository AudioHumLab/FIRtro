#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" 
    Módulo interno usado por server_process.py.
    Maneja las conexiones de entrada al FIRtro para hacer el mono.
    La compensación de niveles al hacer el mono se gestiona en server_process.py.
"""

import jack
from getconfig import *

if load_ecasound:
    firtro_ports = ecasound_ports
else:
    firtro_ports = brutefir_ports

FIRtroInputL, FIRtroInputR = firtro_ports.split()

def setMono(modo):

    jack.attach("tmp")
    
    if modo=='on':

        # leemos los clientes conectados a la entrada del FIRtro
        clientesL = jack.get_connections(FIRtroInputL)
        clientesR = jack.get_connections(FIRtroInputR)
        
        # hacemos el mono añadiendo las conexiones al otro canal:
        for cliente in (clientesL):             # los del IZQ
            jack.connect(cliente, FIRtroInputR) # tambien al DER

        for cliente in (clientesR):             # los del DER
            jack.connect(cliente, FIRtroInputL) # tambien al IZQ

    if modo=='off':

        # nos limitamos a desconectar todo, server_processs se ocupará 
        # de restaurar la entrada vigente.
        clientesL = jack.get_connections(FIRtroInputL)
        clientesR = jack.get_connections(FIRtroInputR)
        for cliente in (clientesL):
            jack.disconnect(cliente, FIRtroInputL)
        for cliente in (clientesR):
            jack.disconnect(cliente, FIRtroInputR)

    jack.detach()

if __name__ == "__main__":
    print __doc__

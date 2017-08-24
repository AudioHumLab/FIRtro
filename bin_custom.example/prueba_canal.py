#!/usr/bin/python
# -*- coding: utf-8 -*-
u""" 
    UNDER CONSTRUCTION

    Script para conectar a la entrada L o R del FIRtro 
    una señal de prueba existente en la entrada analógica L
    
    (i)IMPORTANTE: si se desea medir plano (sin EQ ni DRC),
                   ejecutar antes firtro_bypass.py
    
"""    
import jack
from sys import argv as sys_argv, path as sys_path
sys_path.append("/home/firtro/bin")
from getconfig import *

def desconecta(firtro_ports):
    pass

def conecta(firtro_ports):
    pass

if __name__ == "__main__":
    
    if load_ecasound:
        firtro_ports = ecasound_ports.split()
    else:
        firtro_ports = brutefir_ports.split()

    if sys_argv[1:]:
        for cosa in sys_argv[1:]:
            cosa = cosa.lower()
            if "l" in cosa or "r" in cosa :
                print "EN CONSTRUCCION"
                #desconecta(firtro_ports)
                #print "conectando a " + cosa.upper()
                #conecta(firtro_ports)
    else:
        print __doc__

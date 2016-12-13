#!/usr/bin/python
# -*- coding: utf-8 -*-
u""" 
    Script para gestionar el módulo de reles tosr04.
    
    Uso: reles.py  [cambia | on | off]  [#rele ...] | all]  [--help]
         sin argumentos muestra el estado
         
    NOTA:  se lee un archivo INI con la sección [reles] que 
           etiqueta los reles del modulo de reles:
           /home/firtro/custom/userconfig.ini
          
"""
# v1.0: 

HOME = "/home/firtro"

from sys import argv as sys_argv, exit as sys_exit
from ConfigParser import ConfigParser
firtroINI = ConfigParser()
firtroINI.read("/home/firtro/custom/userconfig.ini")

# https://github.com/amorphic/tosr0x
import tosr0x
# especificamos relayCount=4 para eludir el ciclo inicial
tosr04 = tosr0x.handler(relayCount=4)
misReles = tosr04[0] # es el único que hay conectado
# Diccionario con el estado de los relés
relesStatus = misReles.get_relay_positions()

# Diccionario de reles
relesDic = {}
for rele in firtroINI.options("reles"):
    relesDic[rele] = firtroINI.get("reles", rele)

def get_releKey(etiqueta):
    for x in relesDic.keys():
        if etiqueta in relesDic[x]:
            return x

def set_rele(misreles, comando):
    if "all" in misreles:
        misreles = relesDic.keys()
    for mirele in misreles :
        if comando in ("cambia", "toggle", "conmuta"):
            if relesStatus[int(mirele)]:
                misReles.set_relay_position(int(mirele),0)
            else:
                misReles.set_relay_position(int(mirele),1)
        if comando == "on":
            misReles.set_relay_position(int(mirele),1)
        if comando == "off":
            misReles.set_relay_position(int(mirele),0)

def ver_reles(misreles=relesDic.keys(), printa=True):
    estado = []
    for r in relesStatus:
        tmp = relesStatus[r]
        if printa:
            print "rele: " + str(r), relesDic[str(r)].ljust(12), tmp
        estado.append(tmp)
    return estado
        
if __name__ == "__main__":
    comando = ""
    reles = []
    if sys_argv[1:]:
        for cosa in sys_argv[1:]:
            if cosa in ("cambia", "toggle", "conmuta", "on", "off"):
                comando = cosa
            if cosa in ("1", "2", "3", "4" , "all"):
                reles.append(cosa)
            if "-h" in cosa:
                print __doc__
    else:
        ver_reles()
    
    if comando and reles:
        set_rele(reles, comando)
                

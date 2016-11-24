#!/usr/bin/python
# -*- coding: utf-8 -*-
u""" 
    Script para gestionar la regleta de enchufes.
    
    Uso: regleta.py  [cambia | on | off]  [#toma ...] | all]  [--help]
         sin argumentos muestra el estado
         
    NOTA:  se lee un archivo INI con la sección [regleta] que 
           etiqueta las clavijas de la regleta:
           /home/firtro/custom/firtro.ini
          
"""
# v2.0: 
# reescritura total
# diccionario de clavijas basado en archivo INI

from sys import argv as sys_argv, exit as sys_exit
from subprocess import call, check_output
from ConfigParser import ConfigParser

firtroINI = ConfigParser()
firtroINI.read("/home/firtro/custom/firtro.ini")

# Diccionario de CLAVIJAS
clavijasDic = {}
for clavija in firtroINI.options("regleta"):
    clavijasDic[clavija] = firtroINI.get("regleta", clavija)

# anulado ya que quiero que pueda ser usado por otro usuario,
# por ejemplo www-data de apache2 (botones de la página de control del FIRtro)
#from os.path import expanduser
#HOME = expanduser("~")
HOME = "/home/firtro"

def get_clavijaKey(etiqueta):
    for x in clavijasDic.keys():
        if etiqueta in clavijasDic[x]:
            return x

def set_clavija(misclavijas, comando):
    if "all" in misclavijas:
        misclavijas = clavijasDic.keys()
    for miclavija in misclavijas :
        if comando in ("cambia", "toggle", "conmuta"):
            call("sispmctl -t " + miclavija + " > /dev/null 2>&1", shell=True)
        if comando == "on":
            call("sispmctl -o " + miclavija + " > /dev/null 2>&1", shell=True)
        if comando == "off":
            call("sispmctl -f " + miclavija + " > /dev/null 2>&1", shell=True)

def ver_clavijas(misclavijas=clavijasDic.keys(), printa=True):
    estado = []
    for clavija in misclavijas:
        tmp = check_output("sispmctl -m " + clavija, shell=True).split()[-1]
        if printa:
            print "clavija: " + clavija, clavijasDic[clavija].ljust(6), tmp
        estado.append(tmp)
    return estado
        
if __name__ == "__main__":
    comando = ""
    clavijas = []
    if sys_argv[1:]:
        for cosa in sys_argv[1:]:
            if cosa in ("cambia", "toggle", "conmuta", "on", "off"):
                comando = cosa
            if cosa in ("1", "2", "3", "4" , "all"):
                clavijas.append(cosa)
            if "-h" in cosa:
                print __doc__
    else:
        ver_clavijas()
    
    if comando and clavijas:
        set_clavija(clavijas, comando)
                

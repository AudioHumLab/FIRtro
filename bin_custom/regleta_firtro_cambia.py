#!/usr/bin/python
# -*- coding: utf-8 -*-
u"""
    Script "boton" para apagar/encender:
    - la clavija del AMPlificador en la regleta de enchufes
    - y el audio de FIRtro (para reducir %CPU)
"""
import regleta
import subprocess as sp
from sys import argv as sys_argv, path as sys_path
sys_path.append("/home/firtro/bin/")
import initfirtro
import stopfirtro
from time import sleep

def main():
    for clavija in regleta.clavijasDic.keys():
        if "AMP" in regleta.clavijasDic[clavija].upper():
            if regleta.ver_clavijas(clavija, printa=False) == ["on"]:
                # ^ nota: printa=False para que no printe el estado inicial del enchufe
                regleta.set_clavija(clavija, "off")
                print "Apagamos enchufes y paramos el audio de FIRtro"
                stopfirtro.main("audio")
                return
            else:
                regleta.set_clavija(clavija, "on")
                print "Encendemos enchufes y arrancamos el audio de FIRtro"
                initfirtro.main("audio")
                return
        # retardo necesario para que funcione bien la regleta USB:
        sleep(.2)

if __name__ == '__main__':
    if "-h" in [x for x in sys_argv[1:]]:
        print __doc__
    else:
        main()

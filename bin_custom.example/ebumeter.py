#!/usr/bin/python
# -*- coding: utf-8 -*-

from subprocess import Popen
import sys, time
import jack

def main():

    try:
        # Nos conectamos al servidor jack bajo el nombre "pecador"
        jack.attach("pecador")
    except:
        print "algo va mal no puedorrr conectar a jack"
        sys.exit()

    # Lanzamos ebumeter. Ebumeter no admite argumentos, 
    # requiere conectar sus puertos en jack a posteriori.
    dummy = Popen(["killall", "ebumeter"], stdout=None, stderr=None)
    time.sleep(.5)
    dummy = Popen(["ebumeter"], stdout=None, stderr=None)
    time.sleep(.5)
    
    # Conectamos a Ebumeter los mismos puertos que están conectados a Brutefir:
    conect2ebumeter(BrutefirPorts())

    # Nos desconectamos de Jack
    jack.detach()

def BrutefirPorts():
    L = jack.get_connections('brutefir:input-0')
    R = jack.get_connections('brutefir:input-1')
    return (L,R)

def conect2ebumeter((L_ports,R_ports)):
    # normalmente habrá una pareja de puertos L-R conectada a Brutefir
    for port in L_ports:
        jack.connect(port, 'ebumeter:in.L')
        time.sleep(.1)
    for port in R_ports:
        jack.connect(port, 'ebumeter:in.R')
        time.sleep(.1)

if __name__ == '__main__':
    main()


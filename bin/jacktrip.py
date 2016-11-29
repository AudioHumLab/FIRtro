#!/usr/bin/python
# -*- coding: utf-8 -*-
u"""
    Módulo para gestionar jacktrip en FIRtro.
    https://github.com/jcacerec/jacktrip
    JackTrip ofrece una conexión IP entre dos máquinas que corren JACK,
    sin necesidad de que una de ellas sea esclava con el backend 
    jackd -d net como requieren netjack1 y netjack2.

    IMPORTANTE: Este script evita que algunas versiones Debian/Ubuntu de 
                JackTrip se queden autoconectadas a system:playback_X
                en el momento de inicio de JackTrip.
                Consultar FIRtro -  Guia del Usuario, se recomienda 
                instalar la versión más reciente de JackTrip desde GitHub.
    
    uso:
      jacktrip.py [-s | -c server]  #  modo servidor | modo cliente
      jacktrip.py -r                #  reconecta la entrada actual  a JackTrip:send

    nota:
        Los puertos JackTrip solo pueden conectarse cuando están activos,
        es decir cuando hayan sincronizado con el otro extremo por la red.
"""
# v0.1 BETA -q 8 -r 2 para más robustez en al red
# v0.1a     -z para enviar zeros cuando ocurra underrun
# v0.1b opción -r para reconectar con la entrada activa de FIRtro

from sys import argv as sys_argv, exit as sys_exit
from time import sleep
import jack
import soundcards as sc
from getconfig import *
from subprocess import Popen, check_output

if load_ecasound:
    firtro_ports = ecasound_ports.split()
else:
    firtro_ports = brutefir_ports.split()

def load_jt(options):
    """ arranca jacktrip y lo primero que hacemos es deshacer la conexión 
        automática que jacktrip hace a los puertos system de jack (!)
        Las opciones pueden ser:
        -c remoteHost (modo cliente)
        -s            (modo servidor)
    """
    # muteamos la tarjeta de sonido
    sc.alsa_mute_system_card("on")
    # arranca jacktrip
    Popen("killall jacktrip", shell=True)
    sleep(.5)
    Popen("jacktrip -z -q 8 -r 2 " + options + " >/dev/null 2>&1", shell=True)
    # esperamos a jacktrip:
    intentos = 20 # * 0.25 = 5 segundos
    while intentos:
        try:
            if "JackTrip" in check_output("jack_lsp", shell=True):
                print "(jacktrip.py) Ha arrancado Jacktrip."
                break
        except:
            pass
        intentos -=1
        sleep(.25)
    if not intentos:
        print "(jacktrip.py) Error arrancando Jacktrip"
        sys_exit(-1)
    
    # (!) lo primero deshacemos la conexión automática a system
    jack.attach("tmp")
    jack.disconnect("JackTrip:receive_1", "system:playback_1")
    jack.disconnect("JackTrip:receive_2", "system:playback_2")
    try:
        jack.disconnect("system:capture_1", "JackTrip:send_1")
        jack.disconnect("system:capture_2", "JackTrip:send_2")
    except:
        # es posible que sea un FIRtro pequeño sin system:capture
        pass
    jack.detach()        

    # modo client
    if "-c" in options:
        # La conexión a FIRtro se gestiona cambiando la input en FIRtro. 
        pass

    # modo server
    if "-s" in options:
        connect_source2jacktrip()
            
    sc.alsa_mute_system_card("off")

def connect_source2jacktrip():
        jack.attach("tmp")
        # Desconectamos lo que hubiera en JackTrip
        c1_ports = jack.get_connections("JackTrip:send_1")
        c2_ports = jack.get_connections("JackTrip:send_2")
        for p1 in c1_ports:
            jack.disconnect(p1, "JackTrip:send_1")
        for p2 in c2_ports:
            jack.disconnect(p2, "JackTrip:send_2")
        try:
            # conectamos las fuente del FIRtro a jacktrip
            s1_ports = jack.get_connections(firtro_ports[0])
            s2_ports = jack.get_connections(firtro_ports[1])
            for s1 in s1_ports:
                jack.connect(s1, "JackTrip:send_1")
            for s2 in s2_ports:
                jack.connect(s2, "JackTrip:send_2")
        except:
            # el motivo del fallo es que los puertos de JackTrip no están activos:
            # "Cannot connect ports owned by inactive clients: "JackTrip" is not active"
            # porque no ha sincronizado todavía con un cliente.
            print "(jacktrip.py) (i) para conectar puertos se necesita que estén" 
            print "                  activos (con una conexion cliente jacktrip en red)"
        jack.detach()

if __name__ == "__main__":
    if sys_argv[1:]:
        opts = ""
        for cosa in sys_argv[1:]:
            opts += cosa + " "
        if opts.strip().split()[0] in ("-s", "-c"):
            load_jt(opts)
        elif opts.strip().split()[0] in ("-r"):
            connect_source2jacktrip()
    else:
        print __doc__
    

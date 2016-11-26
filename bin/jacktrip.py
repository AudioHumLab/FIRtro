#!/usr/bin/python
# -*- coding: utf-8 -*-
u"""
    Módulo para gestionar jacktrip en FIRtro.
    JackTrip ofrece una conexión IP entre dos máquinas que corren JACK,
    sin necesidad de que una de ellas sea esclava con el backend 
    jackd -d net como requieren netjack1 y netjack2. 
    
    uso:
        jacktrip.py [-s | -c serverHost]
"""
# v0.1 usar con cautela  :-/
  
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
    Popen("jacktrip -q 8 -r 2 " + options + " >/dev/null 2>&1", shell=True)
    # esperamos a jacktrip:
    intentos = 20 # * 0.25 = 5 segundos
    while intentos:
        try:
            if "JackTrip" in check_output("jack_lsp", shell=True):
                print "(jacktrip) Ha arrancado Jacktrip."
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
        
    # modo client
    if "-c" in options:
        try:
            # lo conectamos al FIRtro, bueno mejor cambiar la input
            #jack.connect("JackTrip:receive_1", firtro_ports[0])
            #jack.connect("JackTrip:receive_2", firtro_ports[1])
            pass
        except:
            Popen("killall jacktrip", shell=True)
            print "(jacktrip) algo va mal :-("

    # modo server
    if "-s" in options:
        try:
            # conectamos las fuente del FIRtro a jacktrip
            source_ports =  [jack.get_connections(firtro_ports[0])[0]]
            source_ports += [jack.get_connections(firtro_ports[1])[0]]
            jack.connect(source_ports[0], "JackTrip:send_1")
            jack.connect(source_ports[1], "JackTrip:send_2")
        except:
            Popen("killall jacktrip", shell=True)
            print "(jacktrip) algo va mal :-("
            
    jack.detach()
    sc.alsa_mute_system_card("off")

if __name__ == "__main__":
    if sys_argv[1:]:
        opts = ""
        for cosa in sys_argv[1:]:
            opts += cosa + " "
        if opts.strip().split()[0] in ("-s", "-c"):
            load_jt(opts)
    else:
        print __doc__
    

#!/usr/bin/env python
#coding=utf-8
# from __future__ import with_statement # This isn"t required in Python 2.6
"""
    Uso:
    stopfirtro.py  [ audio | core | all* ]   (* por defecto)
    audio: Jack, Brutefir, Ecasound.
    core:  + Mpd y otros players, Netjack.
    all:   + Server, Lirc.
"""
# v2.0 
# reordenación del run_level
# reordenación del código evitando líneas multisentencia

import client
import time
import sys
import os
from getconfig import *
from subprocess import *

fnull = open(os.devnull, 'w')

# DEBUG: redirigimos la salida a null, por si falla la llamada client.firtro_socket 
# (descomentar para debug)
# sys.stdout = open(fnull, "w") 

def main(run_level):
    
    if run_level in ["audio", "core", "all"]:
        
        if run_level in ["all"]:
            # lirc
            if load_irexec:
                Popen(["killall", irexec_path], stdout=fnull, stderr=fnull)
            # controlserver
            try:
                client.firtro_socket("quit")
                time.sleep(1)
            except:
                Popen (["pkill", "-9", "-f", control_path], stdout=fnull, stderr=fnull)
                time.sleep(.5)
        
        if run_level in ["core", "all"]:
            # client175
            if load_client175:
                Popen (["pkill", "-9", "-f", client175_path], stdout=fnull, stderr=fnull)
            # mpdlcd (MPD client for lcdproc)
            if load_mpdlcd:
                Popen (["pkill", "-9", "-f", mpdlcd_path], stdout=fnull, stderr=fnull)
            # mpd
            if load_mpd:
                Popen ("killall mpd", shell=True)
            # mopidy
            if load_mopidy:
                Popen (["killall", mopidy_path], stdout=fnull, stderr=fnull)
            # squeezeslave
            if load_squeezeslave:
                Popen (["killall", squeezeslave_path], stdout=fnull, stderr=fnull)
            # shairport
            if load_shairport:
                Popen (["killall", shairport_path], stdout=fnull, stderr=fnull)
            # netjack
            if load_netjack: 
                Popen (["killall", netjack_path], stdout=fnull, stderr=fnull)
            # mplayer
            if load_mplayer_cdda or load_mplayer_tdt: 
                Popen (["killall", mplayer_path], stdout=fnull, stderr=fnull)

        # ecasound
        if load_ecasound:
            Popen (["killall", "-KILL", "ecasound"], stdout=fnull, stderr=fnull)
        # brutefir
        Popen (["killall", brutefir_path], stdout=fnull, stderr=fnull)        
        # jack
        Popen (["killall", "jackd"], stdout=fnull, stderr=fnull)

        time.sleep(1)

    else:
        print __doc__

if __name__ == "__main__":
    if sys.argv[1:]:
        run_level = sys.argv[1].lower()
    else: 
        run_level = "all"
    print "(stopfirtro) deteniendo: " + run_level
    main(run_level)

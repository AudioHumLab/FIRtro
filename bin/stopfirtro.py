#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    'stoptfirtro.py' detiene el server y los módulos de FIRtro.

    Uso:

    stoptfirtro.py [ core | audio | core+players | all ]   (por defecto 'all')

    core o audio:   Jack, Brutefir, Ecasound.
    core+players:   + MPD y otros players
    all:            + control por Lirc y algunos clients para display
"""
# v2.0
#   Reordenación del run_level: core, core+players, all
#   Reescritura del código evitando líneas multisentencia
# v2.0b (revisión)
# v2.0c (revisión)

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
        # client_mpd
            Popen (["pkill", "-9", "-f", "client_mpd.py"], stdout=fnull, stderr=fnull)
        # LCD_server
        if load_LCD_server:
            Popen (["pkill", "-9", "-f", LCD_server_path], stdout=fnull, stderr=fnull)
        # mpdlcd (MPD client for lcdproc)
        if load_mpdlcd:
            Popen (["pkill", "-9", "-f", mpdlcd_path], stdout=fnull, stderr=fnull)
        # INFOFIFO_server
        if load_INFOFIFO_server:
            Popen (["pkill", "-9", "-f", INFOFIFO_server_path], stdout=fnull, stderr=fnull)
        # mpdmonitor
        if load_mpdmonitor:
            Popen (["pkill", "-9", "-f", mpdmonitor_path], stdout=fnull, stderr=fnull)
        # spotifymonitor
        if load_spotifymonitor:
            Popen (["pkill", "-9", "-f", spotifymonitor_path], stdout=fnull, stderr=fnull)

    if run_level in ["core+players", "all"]:
        # mpd
        if load_mpd:
            Popen ("killall mpd", shell=True)
        # mplayer
        if load_mplayer_cdda or load_mplayer_tdt:
            Popen (["killall", mplayer_path], stdout=fnull, stderr=fnull)
        # mopidy
        if load_mopidy:
            Popen (["killall", mopidy_path], stdout=fnull, stderr=fnull)
        # squeezeslave
        if load_squeezeslave:
            Popen (["killall", squeezeslave_path], stdout=fnull, stderr=fnull)
        # shairport
        if load_shairport:
            Popen (["killall", shairport_path], stdout=fnull, stderr=fnull)

    # El core de audio siempre se reinicia:
    # jacktrip
    if load_jacktrip:
        Popen (["killall", jacktrip_path], stdout=fnull, stderr=fnull)
    # netjack
    if load_netjack:
        Popen (["killall", netjack_path], stdout=fnull, stderr=fnull)
    # zita-njbridge
    if load_zita_j2n:
        Popen (["killall", zita_j2n_path], stdout=fnull, stderr=fnull)
    if load_zita_n2j:
        Popen (["killall", zita_n2j_path], stdout=fnull, stderr=fnull)
    # ecasound
    if load_ecasound:
        Popen (["killall", "-KILL", "ecasound"], stdout=fnull, stderr=fnull)
    # brutefir
    Popen (["killall", brutefir_path], stdout=fnull, stderr=fnull)
    # jack
    Popen (["killall", "jackd"], stdout=fnull, stderr=fnull)

    time.sleep(1)


if __name__ == "__main__":

    run_level = "all"
    if sys.argv[1:]:
        run_level = sys.argv[1].lower()

    if run_level == "audio": # alias
        run_level = "core"

    if run_level in ["audio", "core+players", "all"]:
        print "(stopfirtro) deteniendo: " + run_level
        main(run_level)
    else:
        print __doc__

#!/usr/bin/env python
# -*- coding: utf-8 -*-

# v1.0b
# Sale del loop si se pierde la conexión con MPD

###
# The mpd2 library:
# http://pythonhosted.org/python-mpd2/topics/getting-started.html
# http://pythonhosted.org/python-mpd2/topics/commands.html
###

import os
import mpd # mpd is replaced by python-mpd2
import client as firtroClient
from math import log

# Slider volume range as per audio/config
from getconfig import mpd_volume_slider_range as slider_range
slider_range = abs(int(slider_range)) # Must be positive integer

def connect_mpd(mpd_host=None, mpd_port=None, mpd_passwd=None):
    """Connect to mpd.
    """
    client = mpd.MPDClient()
    if mpd_host == None:
        mpd_host = os.getenv('MPD_HOST')
    if mpd_host is None:
        mpd_host = 'localhost'
    else:
        splithost = mpd_host.split('@')
        if len(splithost) > 1:
            mpd_passwd = splithost[0]
            mpd_host = splithost[1]
    mpd_port = os.getenv('MPD_PORT')
    if mpd_port is None:
        mpd_port = 6600
    client.connect(mpd_host, mpd_port)
    if mpd_passwd is not None:
        client.password(mpd_passwd)
    return client

def idle_loop(c):
    """MPD idle loop (daemon mode)
    """
    while True:

        # https://pythonhosted.org/python-mpd2/topics/commands.html
        #'MPDClient.idle(sub1, ...)' waits for a MPD change on the indicated subsystems* ...
        # ... when something happens, idle ends, then this script continues.
        # (*) 'mixer' filters only volume events.
        try:
            c.idle('mixer')
        except:
            print "(client) Terminado. se ha perdido la conexión con MPD."
            raise SystemExit, 0

        newVol = c.status()['volume']
        # set FIRtro gain:
        g = str(int(round(((log(1+float(newVol)/100)/log(2))**1.293-1)*slider_range)))
        firtroClient.firtro_socket("gain " + g, quiet=True)

def setvol(vol):
    try:
        c = connect_mpd()
        c.setvol(int(vol))
        c.close()
        c.disconnect()
    except:
        print "(client_mpd) Ha habido un problema intentando establecer el volumen en MPD."

if __name__ == "__main__" or __name__ == "main":

    c = connect_mpd()
    c.timeout = 10
    c.idletimeout = None
    idle_loop(c)
    c.close()
    c.disconnect()

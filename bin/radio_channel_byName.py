#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" 
    FIRtro 2.0. Script para cambiar de canal DVB-Radio (tdt)
    Uso:
        radiochannel.py [ nombreCanal | -last | -prev ]
    Nota:
        nombreCanal segun:
            ~/audio/radio
            ~/.mplayer/channels.conf
""" 
# v1.0b
# - se adopta el archivo original de canales ~/audio/radio

import os
from subprocess import call as sp_call
from sys import argv as sys_argv, path as sys_path
sys_path.append("/home/firtro/bin")
from getconfig import tdt_fifo
from basepaths import status_filename
from ConfigParser import ConfigParser
userConfig = ConfigParser()
userConfigF  = "/home/firtro/audio/radio"
status = ConfigParser()
statusFile = "/home/firtro/audio/status"
mplayerChannelsFile = ("/home/firtro/.mplayer/channels.conf")

# Para las funciones last_channel() y prev_channel()
from ConfigParser import ConfigParser
st = ConfigParser()
def read_status():
    st.read("/home/firtro/audio/" + status_filename)
    global radioch, radioch_prev
    radioch      = st.get("inputs", "radioch")
    radioch_prev = st.get("inputs", "radioch_prev")

def last_channel():
    read_status()
    if not select_channel(radioch):
        print "error recuperando last channel"

def prev_channel():
    read_status()
    if not select_channel(radioch_prev):
        print "error recuperando previous channel"

def userChannels():
    """ Lee los canales de userconfig.ini
    """
    canales = []
    userConfig.read(userConfigF)
    for option in userConfig.options("channels"):
        canalName = userConfig.get("channels", option)
        canales.append( canalName.replace('"', '').replace("'", "").strip() )
    return canales

def mplayerChannels():
    """ Lee los canales en .mplayer/channels.conf
    """
    chs = []
    try:
        f = open(mplayerChannelsFile, "r")
        for cosa in f.readlines():
            chs.append(cosa.split(":")[0])
        f.close()
    except:
        print "problemas accediendo a " + mplayerChannelsFile
    return chs

def select_channel(ch):
    """ cambia de canal si el canal está en userconfig.ini o en channels.conf
    """
    if ch in userChannels() or ch in mplayerChannels():
        # hay que escapar los espacios para mplayer:
        ch2 = ch.replace(" ", "\\ ")
        tmp = "echo loadfile dvb://'" + ch2 + "' > " + tdt_fifo
        sp_call(tmp + "&", shell=True)
        # actualizamos status con  el canal solicitado a mplayer
        updateStatus(ch)
        return True
    else:
        return False

def updateStatus(ch):
    status.read(statusFile)
    prev = status.get("inputs", "radioch")
    if prev <> ch:
        status.set("inputs", "radioch_prev", prev) 
    status.set("inputs", "radioch", ch) 
    f = open(statusFile, "w")
    status.write(f)
    f.close()

if __name__ == "__main__":
    if sys_argv[1:]:
        canal = sys_argv[1]
        if canal == "-last":
            last_channel()
        elif canal == "-prev":
            prev_channel()
        elif not select_channel(canal):
            print "NO existe el canal:", canal
    else:
        print __doc__
        

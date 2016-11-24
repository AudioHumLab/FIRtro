#!/usr/bin/python
# -*- coding: utf-8 -*-
u""" 
    FIRtro 2.0. Script para cambiar de canal DVB-Radio (tdt)
    Uso:
        radiochannel.py nombreCanal
    Nota:
        nombreCanal según:
            ~/custom/firtro.ini
            ~/.mplayer/channels.conf
"""    
   
import os
from subprocess import call as sp_call
from sys import argv as sys_argv, path as sys_path
import subprocess as sp
sys_path.append("/home/firtro/bin")
from getconfig import tdt_fifo

from ConfigParser import ConfigParser
myChannels  = ConfigParser()
configFile = "/home/firtro/custom/firtro.ini"
status = ConfigParser()
statusFile = "/home/firtro/audio/status"
mplayerChannelsFile = ("/home/firtro/.mplayer/channels.conf")

def misCanales():
    """ Lee los canales de firtro.ini
    """
    canales = []
    myChannels.read(configFile)
    for option in myChannels.options("tdtradio"):
        canalName = myChannels.get("tdtradio", option)
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

def selec_canal(c):
    """ cambia de canal si el canal está en firtro.ini o en channels.conf
    """
    if c in misCanales() or c in mplayerChannels():
        c = c.replace(" ", "\\ ") # hay que escapar los espacios para mplayer
        tmp = "echo loadfile dvb://'" + c + "' > " + tdt_fifo
        sp_call(tmp + "&", shell=True)
        return True
    else:
        return False

def actualizaStatus(c):
    status.read(statusFile)
    prev = status.get("inputs", "radioch")
    if prev <> c:
        status.set("inputs", "radioch_prev", prev) 
    status.set("inputs", "radioch", c) 
    f = open(statusFile, "w")
    status.write(f)
    f.close()

if __name__ == "__main__":
    if sys_argv[1:]:
        canal = sys_argv[1]
        if selec_canal(canal):
            actualizaStatus(canal)
        else:
            print "NO existe el canal:", canal

    else:
        print __doc__
        

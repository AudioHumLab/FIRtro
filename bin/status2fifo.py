#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
    Devuelve una composición de 4 lineas que resume el estado de FIRtro:
"""

# v1.0

import json
from getstatus import *

def jsonStatus2fifo(jstatus):
    s = json.loads(jstatus)
 
    # Algunas adecuaciones:
    sEQ =       "     "
    DRC =       "   "
    pEQ =       "   "
    Loudness =  "    "
    Stereo =    "Stereo"
    if not s['muted']:
        Vol = str(s['level'])
    else:
        Vol = "MUTE"
    Hr   =  str(int(s['headroom'])).rjust(2)
    Bal  =  str(int(s['balance'] )).rjust(2)
    Bass =  str(int(s['bass']    )).ljust(2)
    Treb =  str(int(s['treble']  )).ljust(2)
    input_name = s['input_name']
    preset = s['preset']
    filter_type = s['filter_type']

    if s['system_eq']:                          sEQ = "SysEQ"
    if s['drc_eq'] <> "0":                      DRC = "DRC"
    if s['peq'] <> '' and not s['peqdefeat']:   pEQ = "PEQ"
    if s['loudness_track']:                     Loudness = "LOUD"
    if s['mono'] == "on":                       Stereo = "MONO"

    d = {'Vol':         Vol,
         'Hr':          Hr,
         'Bal':         Bal,
         'Bass':        Bass,
         'Treb':        Treb,
         'sEQ':         sEQ,
         'DRC':         DRC,
         'pEQ':         pEQ,
         'Loudness':    Loudness,
         'Stereo':      Stereo,
         'input':       input_name,
         'preset':      preset,
         'filter_type': filter_type}

    return _dic2infofifo(d)

def audioStatus2fifo():
    # se lee el fichero de estado de FIRtro
    statusfile = open(status_path)
    status.readfp(statusfile)
    statusfile.close

    # Algunas adecuaciones:
    sEQ =       "     "
    DRC =       "   "
    pEQ =       "   "
    Loudness =  "    "
    Stereo =    "Stereo"
    if not muted:
        Vol = str(level)
    else:
        Vol = "MUTE"
    Hr   =  str(int(headroom)).rjust(2)
    Bal  =  str(int(balance)).rjust(2)
    Bass =  str(int(bass)).ljust(2)
    Treb =  str(int(treble)).ljust(2)

    if system_eq == "True":
       sEQ = "SysEQ"
    if drc_eq <> "0":
        DRC = "DRC"
    if peq <> "" and peqdefeat == "False":
        pEQ = "PEQ"
    if loudness_track:
        Loudness = "LOUD"
    if mono == "on":
        Stereo = "MONO"

    d = {'Vol':         Vol,
         'Hr':          Hr,
         'Bal':         Bal,
         'Bass':        Bass,
         'Treb':        Treb,
         'sEQ':         sEQ,
         'DRC':         DRC,
         'pEQ':         pEQ,
         'Loudness':    Loudness,
         'Stereo':      Stereo,
         'input':       input_name,
         'preset':      preset,
         'filter_type': filter_type}

    return _dic2infofifo(d)

def _dic2infofifo(d):

    # --- ESQUEMA:
    #    0         1        2         3
    #    12345678901234567890123456789012
    # 0  --------------------------------
    # 1  Vol: -32.0   Hr: 34.0     Bal -2
    # 2  Bass: -2 Treb: -3  SysEQ DRC PEQ
    # 3  I: input_name       LOUD  Stereo
    # 4  P: preset_name         ftype: mp
    # 5  --------------------------------

    l0 = "-" * 32
    l5 = "-" * 32

    l1 =  ("Vol: " + d['Vol']).ljust(13)
    l1 += ("Hr: " + d['Hr']).ljust(12)
    l1 += ("Bal: " + d['Bal']).rjust(7)

    l2 =  ("Bass: " + d['Bass']).ljust(9)
    l2 += ("Treb: " + d['Treb']).ljust(9)
    l2 += d['sEQ'].rjust(6)
    l2 += d['DRC'].rjust(4)
    l2 += d['pEQ'].rjust(4)

    l3 =  ("I: " + d['input']).ljust(19) + " "
    l3 += d['Loudness'].ljust(6)
    l3 += d['Stereo'].rjust(6)

    l4 =  ("P: " + d['preset']).ljust(23)
    l4 += ("ftype: " + d['filter_type']).rjust(9)

    return "\n".join((l0, l1, l2, l3, l4, l5))

if __name__ == "__main__":
    print __doc__
    print audioStatus2fifo()

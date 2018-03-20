#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    v0.1beta
    cutre script para gobernar el volumen de FIRtro mediante un ratón

    left button   -->  vol --
    right button  -->  vol ++
    wheel         -->  togles mute

"""
##################
SALTOdBs = 2
##################

import sys, os
import binascii
HOME = os.path.expanduser("~")
fmice = open( "/dev/input/mice", "rb" );

def getMouseEvent():
    # leeemos el mice por bloques de bytes, la longitud
    # depende del raton, en mi caso son tres bytes
    buff = fmice.read(3);
    m = binascii.hexlify(buff)
    # print m # debug
    if   m == "090000":
        return "buttonLeftDown"
    elif m == "0a0000":
        return "buttonRightDown"
    elif m == "0c0000":
        return "wheelDown"

for opc in sys.argv:
    if "-h" in opc:
        print __doc__
        sys.exit()

while True:
    ev = getMouseEvent();
    if   ev == "buttonLeftDown":
        os.system("control level_add -" + str(SALTOdBs))
    elif ev == "buttonRightDown":
        os.system("control level_add +" + str(SALTOdBs))
    elif ev == "wheelDown":
        os.system("control toggle") # mute / unmute

fmice.close();

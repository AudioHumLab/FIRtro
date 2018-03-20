#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    v0.1beta
    cutre script para gobernar el volumen de FIRtro mediante un ratón

    left button   -->  vol --
    right button  -->  vol ++
    mid button    -->  togles mute
    
    Permisos de acceso: el usuario 'firtro' debe incluirse en el grupo 
    que tiene acceso a /dev/input/xxxx
    (está definido en /etc/udev/rules.d/99-input.rules)
    
    Por ejemplo
    ~ $ ls -l /dev/input/
    total 0
    crw-rw---- 1 root input 13, 64 Mar 19 20:53 event0
    crw-rw---- 1 root input 13, 63 Mar 19 20:53 mice
    crw-rw---- 1 root input 13, 32 Mar 19 20:53 mouse0

    /dev/input/mouseX is a stream of 3 bytes: [Button_value] [XX_value] [YY_value]

    You would get a 4 byte stream if the mouse is configured with the scroll wheel (intellimouse)

    /dev/input/mice emulates a PS/2 mouse in three-byte mode.

        0x09XXYY --> buttonLeftDown 
        0x0aXXYY --> buttonRightDown
        0x0cXXYY --> wheelDown

    Para ver la correspondecia de los archivos /dev/input/xxxxx
        $ cat /proc/bus/input/devices
        I: Bus=0003 Vendor=046d Product=c03d Version=0110
        N: Name="Logitech USB-PS/2 Optical Mouse"
        P: Phys=usb-3f980000.usb-1.2/input0
        S: Sysfs=/devices/platform/soc/3f980000.usb/usb1/1-1/1-1.2/1-1.2:1.0/0003:046D:C03D.0001/input/input0
        U: Uniq=
        H: Handlers=mouse0 event0
        B: PROP=0
        B: EV=17
        B: KEY=70000 0 0 0 0 0 0 0 0
        B: REL=103
        B: MSC=10

"""
##################
SALTOdBs = 2
##################

import sys, os
# import struct
import binascii
HOME = os.path.expanduser("~")
fmice = open( "/dev/input/mice", "rb" );

def getMouseEvent():
    # /dev/input/mice is a PS/2 emulation of 3 bytes: [Button] [XX_value] [YY_value]
    buff = fmice.read(3);
    # print struct.unpack('3b', buff)  # Unpacks the bytes to integers
    m = binascii.hexlify(buff)
    # print m # debug
    if   m == "090000":
        return "buttonLeftDown"
    elif m == "0a0000":
        return "buttonRightDown"
    elif m == "0c0000":
        return "midButton"

for opc in sys.argv:
    if "-h" in opc:
        print __doc__
        sys.exit()

while True:
    # leemos el ratón
    ev = getMouseEvent();
    
    # enviamos la orden correspondiente a FIRtro
    if   ev == "buttonLeftDown":
        os.system("control level_add -" + str(SALTOdBs))    # level --
    elif ev == "buttonRightDown":
        os.system("control level_add +" + str(SALTOdBs))    # level ++
    elif ev == "midButton":
        os.system("control toggle")                         # mute / unmute

fmice.close();

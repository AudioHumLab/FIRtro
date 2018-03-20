#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    v0.3beta
    Cutre script para gobernar el volumen de FIRtro mediante un ratón

    Uso:
            mouse_volume_daemon.py [-sNN -bHH] &

                -sNN volume step NN dBs (default 2.0 dB)
                -bHH beep si excedemos headroom HH dB (default 6.0 dB)
                -h   this help

                left button   -->  vol --
                right button  -->  vol ++
                mid button    -->  togles mute

    Notas:

    Permisos de acceso: el usuario 'firtro' debe incluirse en el grupo
    que tiene acceso a /dev/input/xxxx
    (está definido en /etc/udev/rules.d/99-input.rules)

    Por ejemplo aquí el grupo sería 'input':
    ~ $ ls -l /dev/input/
    total 0
    crw-rw---- 1 root input 13, 64 Mar 19 20:53 event0
    crw-rw---- 1 root input 13, 63 Mar 19 20:53 mice
    crw-rw---- 1 root input 13, 32 Mar 19 20:53 mouse0

"""
# v0.2beta: beeps con un synth de SoX (play)
# v0.3beta: beeps en un aviso.wav con aplay

import sys, os, time
import subprocess as sp
import binascii
#import struct

def getMouseEvent():
    """
    /dev/input/mouseX is a stream of 3 bytes: [Button_value] [XX_value] [YY_value]

    You would get a 4 byte stream if the mouse is configured with the scroll wheel (intellimouse)

    /dev/input/mice emulates a PS/2 mouse in three-byte mode.

        0x09XXYY --> buttonLeftDown
        0x0aXXYY --> buttonRightDown
        0x0cXXYY --> buttonMid

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
    buff = fmice.read(3);
    m = binascii.hexlify(buff)
    #print m, struct.unpack('3b', buff)  # Unpacks the bytes to integers
    if   m[:2] == "09":
        return "buttonLeftDown"
    elif m[:2] == "0a":
        return "buttonRightDown"
    elif m[:2] == "0c":
        return "buttonMid"

def check_headroom():
    # Como status puede esar bloqueado por escritura desde el server,
    # a veces ocurre un error al extraer 'headroom'
    i = 0
    while i < 20:
        f = open("/home/firtro/audio/status", "r")
        conte = f.read()
        f.close()
        try:
            headroom = conte.split("headroom")[1].split()[1]
            return float(headroom)
        except:
            pass
        i += 1
        time.sleep(.2)
    return 0.0

def pita():
    # El sinte de SoX (play) es lento
    #os.system("play --null synth 1 sine 880 gain -10.0 > /dev/null 2>&1")
    # Usamos un aviso.wav
    os.system("aplay -Djack /home/firtro/bin_custom/aviso.wav > /dev/null 2>&1")

if __name__ == "__main__":

    HOME = os.path.expanduser("~")
    fmice = open( "/dev/input/mice", "rb" );

    SALTOdBs = 2.0
    HRthr    = 6.0
    pitar = False

    for opc in sys.argv:
        if "-h" in opc:
            print __doc__
            sys.exit()
        if "-b" in opc:
            pitar = True
        if "-s" in opc:
            try:
                SALTOdBs = float(opc.replace("-s", ""))
            except:
                pass
        if "-b" in opc:
            try:
                HRthr = float(opc.replace("-b", ""))
            except:
                pass

    level_ups = False
    ha_pitado = False
    while True:
        # leemos el ratón
        ev = getMouseEvent();

        # enviamos la orden correspondiente a FIRtro
        if   ev == "buttonLeftDown":
            sp.call("control level_add -" + str(SALTOdBs), shell=True)    # level --
            level_ups = False
        elif ev == "buttonRightDown":
            sp.call("control level_add +" + str(SALTOdBs), shell=True)    # level ++
            level_ups = True
        elif ev == "buttonMid":
            sp.call("control toggle", shell=True)                         # mute / unmute

        # pitido de alerta si cruzamos headroom
        if level_ups:
            hr = check_headroom()
            if hr < HRthr:
                print hr
                if not ha_pitado and pitar:
                    pita()
                    ha_pitado = True
            else:
                ha_pitado = False

    fmice.close();


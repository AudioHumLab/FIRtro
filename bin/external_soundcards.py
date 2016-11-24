#!/usr/bin/python
# -*- coding: utf-8 -*-

""" Módulo interno usado por initfirtro y por server_inputs.
    OjO las tarjetas que se manejan aquí serán las definidas en 
    ~/audio/config, referidas siempre con el descriptor ALSA completo,
    por ejemplo:    "hw:PCH,1"  ó  "hw:miniStreamer,0"
    
    v1.1: 
    Se evalúa si la tarjeta es USB (aplay -l) para poner n=3 en zita
    Se pone latencia inicial en zita-a2j para intentar evitar desincronismos
"""

from time import sleep
import jack
import os
import subprocess as sp
from sys import path as sys_path
HOME = os.path.expanduser("~")
sys_path.append(HOME + "/bin")
from getconfig import *

# Puertos JACK de monitores de la señal definidos en audio/config
monitor_ports = jack_external_monitors.split() + jack_internal_monitors.split()

# Funcion para resincronizar posibles tarjetas externas usadas
# como entrada de señal, típicamente SPDIF que requerirá resincronización.
def external_card_resync(in_ports, rate):
    card_es_input_y_monitor = False
    # recorremos las tarjetas externas declaradas en el FIRtro
    for card in external_cards.split():

        # Evaluamos si la tarjeta proporciona los puertos jack para la input requerida
        if [x for x in in_ports if bareCard(card) in x]:

            # Evaluamos si la tarjeta tb se emplea como monitor, en ese caso lo
            # suyo es rearrancar zita-j2a con la nueva rate en esa tarjeta
            if [x for x in monitor_ports if bareCard(card) in x]:
                card_es_input_y_monitor = True

            apaga_zita(card)
            if card_es_input_y_monitor:
                arranca_zita(card, rate, mode="j2a")
            arranca_zita(card, rate, mode="a2j")

def apaga_zita(card):
    sp.call("pkill -f " + card , shell=True)
    intentos = 8
    while True:
        zita_process = sp.check_output("pgrep -l -f " + bareCard(card), shell=True)
        if not "zita" in zita_process:
            print "(server_input) Se ha apagado zita " + card
            break
        if not intentos:
            print "(server_input) <!> no se ha apagado zita " + card
            break
        intentos -= 1
        sleep(.25)

def bareCard(card):
    """ función auxiliar que devuelve el nombre de la tarjeta 
        sin "hw:" y sin el device ",X"
        de utilidad para presentar la tarjeta en jack o para buscarla
        dentro de los posibles monitores externos de audio/config
    """
    bareCard = card.split(":")[-1] # quitamos "hw:" si lo hubiera
    return bareCard.split(",")[0]  # y el device ",X" si lo hubiera...

def cardIsUSB(card):
    tmp = sp.check_output("aplay -l | grep " + bareCard(card), shell=True)
    if "usb" in tmp.lower():
        return True
    else:
        return False

def temporary_zita_bash(card, rate, mode, p="512", n="2"):
    """ OjO algo pasa con zita que deja el socket 9999 pillado si lo intentamos lanzar desde python
        He optado por preparar un script de shell e invocarlo, entonces no hay problema (¿¡?)
    """
    latencia = ""
    if mode == "a2j":
        latencia = " -I512" # ver man zita-a2j
    if cardIsUSB(card):
        n = "3"
        p = "1024"
    tmp =  "# OjO algo pasa con zita que deja el socket 9999 pillado si lo intentamos lanzar desde python\n"
    tmp += "# He optado por preparar un script de shell e invocarlo, entonces no hay problema (¿¡?)\n"
    tmp += "zita-" + mode + " -j" + bareCard(card) + " -d" + card + latencia + \
           " -L -p" + p + " -n" + n + " -r" + rate + " > /dev/null 2>&1 &"
    os.system("touch    /tmp/zitaTmp.sh")
    os.system("chmod +x /tmp/zitaTmp.sh")
    os.system("echo '" + tmp + "' > /tmp/zitaTmp.sh")
    sp.call  ("/tmp/zitaTmp.sh", shell=True)
    os.remove("/tmp/zitaTmp.sh")  # lo borramos para que otro usuario pueda sobreescribirlo later

def arranca_zita(card, rate, mode):

    temporary_zita_bash(card, rate, mode)

    # esperamos a que los puertos zita aparezcan en jack
    jack.attach('tmp')
    intentos = 8; encontrado = False
    while True:
        for port in jack.get_ports():
            if bareCard(card) in port:
                encontrado = True
        if encontrado:
            print "(server_input) Se ha reiniciado zita-" + mode + " " + card + " " + rate
            break
        if not intentos:
            print "(server_input) <!> No se ha podido reiniciar zita-" + mode + " " + card + " " + rate
            break
        intentos -= 1
        print "(server_input) Esperando a zita-" + mode + " . .. ..."
        sleep(.25)
    jack.detach()

if __name__ == "__main__":
    print __doc__
    print "    External cards definidas en ~/audio/config:"
    for card in external_cards.split():
        print "\t" + card
    print
    

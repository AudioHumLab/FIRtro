#!/usr/bin/python
# -*- coding: utf-8 -*-
u""" 
    Módulo interno para gestión de las tarjetas declaradas en 
    ~/audio/config
    
    - Gestión del mixer de las tarjetas.
    - Integración en Jack mediante resampling (zita).
    - Gestión del reloj en tarjetas profesionales.
    
    NOTA:
    Las tarjetas profesionales con referencia de reloj configurable (int/ext) 
    deben ser declaradas en /home/firtro/audio/cards.ini (ver documentación)
"""    
# v1.1: 
# - Se evalúa si la tarjeta es USB (aplay -l) para poner n=3 en zita
# - Se pone latencia inicial en zita-a2j para intentar evitar desincronismos
# v1.2:
# - Se integra aquí la funcionalidad de selección de la referencia de reloj
#   interna/externa para tarjetas profesionales compatibles.
# v1.3:
# - Se integran aquí las funciones para restaurar el mixer ALSA de las [cards] 
#   de audio/config, también para hacer mute/unmute en el mixer de la principal.
# v1.3a
# - Se revisa la rutina alsa_mute_system_card() 
# - Se permite un argumento (no documentado) que fuerza un flapeo SPDIF 
#   para intentar resincronizar el DAC externo conectado :-/
# v1.3b
# - se depura iec958_set para tarjetas que no tengan este control
# v1.3c
# - se depura analog_scontrols y iec_scontrols
   
from time import sleep
import jack
import os
from sys import argv as sys_argv
import subprocess as sp
from getconfig import *
from ConfigParser import ConfigParser
cardsINI = ConfigParser()
cardsINI.read("/home/firtro/audio/cards.ini")

##############################################################################
#                       CONFIGURABLE PARA DEVELOPPERS:                       #
#  DICCIONARIO DE FUNCIONES PARA TARJETAS CON REFERENCIA DE RELOJ INT/EXT    #
#                              (ver más abajo)                               #
##############################################################################

# Puertos JACK de monitores de la señal definidos en audio/config
monitor_ports = jack_external_monitors.split() + jack_internal_monitors.split()

# rutina para lanzar comandos amixer
def amixer(card, cmd):
    cmd = "amixer -q -c" + card + " " + cmd
    if sp.call(cmd, shell=True):
        print "(soundcards) <!> Error: " + cmd
        return False
    else:
        print "(soundcards) " + cmd
        return True
    
# Función especializada en la tarjeta M-Audio 1010LT
def change_clock_1010LT(clock,fs):
    """ Orden de configuracion:
        'Multi Track Internal Clock Default' --> 'valor_Fs'
        'Multi Track Internal Clock'         --> 'valor_Fs' o 'IEC958 Input'
    """
    cmd = "sset 'Multi Track Internal Clock Default' '" + format(fs) + "'"
    chk1 = amixer("M1010LT", cmd)
    if clock == "card":
        cmd = "sset 'Multi Track Internal Clock' '" + format(fs) + "'"
        chk2 = amixer("M1010LT", cmd)
    elif clock == "spdif":
        cmd = "sset 'Multi Track Internal Clock' 'IEC958 Input'"
        chk2 = amixer("M1010LT", cmd)
    else:
        chk2 = False
    return chk1 and chk2

# Función especializada en NO HACER NADA (es para probar el diccionario)
def change_clock_DUMMY(clock,fs):
    print "(soundcards) change clock *** DUMMY *** clock:" + clock + " fs:" + format(fs)
    return True
    
# DICCIONARIO DE FUNCIONES PARA TARJETAS CON REFERENCIA DE RELOJ INT/EXT
# De uso interno para apuntar a la función correspondiente
# para las tarjetas [proCards] en ~/audio/cards.ini.
# Las funciones especializadas para cada tarjeta se deben definir antes que este diccionario.
fDict = { "M1010LT" : change_clock_1010LT,
          "DX"      : change_clock_DUMMY
        }

# Función genérica para cambiar la referencia de reloj de tarjetas profesionales compatibles
def change_clock(clock, fs, card=system_card):
    """ con opción de cambiar la tarjeta afectada para debug
    """
    if clock in ("spdif", "card"):
        if "proCards" in cardsINI.sections():
            if bareCard(card) in cardsINI.get("proCards", "cards").split():
                fDict[bareCard(card)](clock, fs)
            else:
                print "(soundcards) <!> Clock option not available on " + card
                return False
    else:
        print "(soundcards) <!> ERROR valid clock values are: spdif | card"
        return False

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

# devuelve el nombre alsa de la tarjeta sin "hw:_____,X"
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
    if sp.call  ("/tmp/zitaTmp.sh", shell=True):
        chk = False
    else: 
        chk = True
    os.remove("/tmp/zitaTmp.sh")  # lo borramos para que otro usuario pueda sobreescribirlo later
    return chk
    
def arranca_zita(card, rate, mode):
    if temporary_zita_bash(card, rate, mode):
        # esperamos a que los puertos zita aparezcan en jack
        jack.attach('tmp')
        intentos = 8; encontrado = False
        while True:
            for port in jack.get_ports():
                if bareCard(card) in port:
                    encontrado = True
            if encontrado:
                print "(soundcards) Se ha reiniciado zita-" + mode + " " + card + " " + rate
                break
            if not intentos:
                print "(soundcards) <!> No se ha podido reiniciar zita-" + mode + " " + card + " " + rate
                break
            intentos -= 1
            print "(soundcards) Esperando a zita-" + mode + " . .. ..."
            sleep(.25)
        jack.detach()
    else:
        print "(soundcards) <!> No se ha podido reiniciar zita-" + mode + " " + card + " " + rate
        
def alsa_restore_cards():
    """ Restaura los amixer de todas las tarjetas de ~/audio/config leyendo
        los archivos asound.XXXX que el usuario ha debido guardar en ~/audio
    """
    for card in [system_card] + external_cards.split():
        card = bareCard(card)
        tmp = "alsactl --file /home/firtro/audio/asound." + card + " restore " + card
        print "cccc", card
        tmp = sp.call(tmp, shell=True)

def alsa_mute_system_card(muteOnOff):
    """ Gestiona el MUTE amixer la tarjeta principal del FIRtro.
    """
    card = bareCard(system_card)
    if muteOnOff == "on":   mode = "off" # va con lógica inversa
    else:                   mode = "on"
    # Las salidas analógicas:
    # amixer(card, cmd="sset Master playback '" + mode + "'")
    analog_set(card, mode)
    # y las SPDIF (si las tuviera conmutables):
    iec958_set(card, mode)

def alsa_dB2percent(dB):
    """ truño ya que no funciona el comando amixer sset ... -3dB
        solo funciona bien dando un % que baje 10 puntos cada -3 dBs (!)
    """
    tmp = float(dB.replace("dB", ""))
    tmp = int(100.0 + (tmp * 10.0/3.0))
    if tmp < 0:
        tmp = 0
    return str(tmp) + "%"

def analog_set(card=bareCard(system_card), mode="off"):
    """ Función auxiliar para establecer los controles principales analógicos (Master o DAC)
    """
    if mode == "off":
        for scontrol in analog_scontrols_main(card):
            cmd = "-M sset " + scontrol + " 0%"
            amixer(card, cmd)
    if mode == "on":
        for scontrol in analog_scontrols_main(card):
            gain = "0.00dB"
            # (i) LEEMOS ~/audio/cards.ini si tuviera una sección para la tarjeta
            if card in cardsINI.sections():
                gain = cardsINI.get(card, scontrol)
            cmd = "-M sset " + scontrol + " " + alsa_dB2percent(gain)
            amixer(card, cmd)

def analog_scontrols_main(card=bareCard(system_card)):
    """ v1.0 solo buscamos los DAC o los Master
    """
    try:
        tmp = sp.check_output("amixer -c" + bareCard(card) + " scontrols | grep -i dac", shell=True).split("\n")[:-1]
        DACs = [x.split("control ")[-1] for x in tmp if not "filter" in x.lower()]
    except:
        DACs = []
    try:
        tmp = sp.check_output("amixer -c" + bareCard(card) + " scontrols | grep -i master", shell=True).split("\n")[:-1]
        Masters = [x.split("control ")[-1] for x in tmp]
    except:
        Masters = []
    return DACs + Masters

def iec958_set(card=bareCard(system_card), mode="on"):
    """ Función auxiliar para establecer los posibles switches SPDIF de una tarjeta
    """
    for scontrol in iec958_scontrols(card):
        # Solo lo ejecutamos si el scontrol tiene Capabilities: pswitch (los penum no funcionan)
        # y excluimos los loopback
        if "pswitch" in sp.check_output("amixer -c" + bareCard(card) + " sget " + scontrol, shell=True):
            amixer(card, cmd="sset " + scontrol + " '" + mode + "'")

def iec958_scontrols(card=bareCard(system_card)):
    try:
        tmp = sp.check_output("amixer -c" + bareCard(card) + " scontrols | grep -i iec958", shell=True).split("\n")[:-1]
        tmp = [x.split("control ")[-1] for x in tmp]
        return [x for x in tmp if (not "loop" in x.lower()) and (not "filter" in x.lower())]
    except: 
        return []
        
if __name__ == "__main__":
    if sys_argv[1:]:
        for cosa in sys_argv[1:]:
            cosa = cosa.lower()
            if "spdif" in cosa or "iec958" in cosa or "reset" in cosa:
                print "forzamos un flapeo SPDIF para intentar resincronizar el DAC externo :-/"
                sleep(.05)
                iec958_set(bareCard(system_card), "off")
                sleep(.05)
                iec958_set(bareCard(system_card), "on")
    else:
        print __doc__
        print   "    'system card' declarada en ~/audio/config:"
        print "\t" + system_card
        print "\n    'external_cards' declaradas en ~/audio/config:"
        for card in external_cards.split():
            print "\t" + card
        if "proCards" in cardsINI.sections():
            print "\n    Tarjetas profesionales con referencia de reloj configurable:"
            print "\t(~/audio/cards.ini)"
            for card in cardsINI.get("proCards", "cards").split():
                print "\t" + card
        print
    

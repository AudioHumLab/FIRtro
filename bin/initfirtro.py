#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    Uso:
    initfirtro.py [ audio | core | all* ]   (* por defecto)
    audio: Jack, Brutefir, Ecasound.
    core:  + Mpd y otros players, Netjack.
    all:   + Server, Lirc.
"""
#----------------------------------------------------------------------
# v2.0 (2016-nov)
#
# - "soundcards" (aka sc) se usa para:
#   - tarjetas de sonido adicionales definidas en audio/config
#     para entradas adicionales o para monitoreo externo.
#   - recuperar el alsamixer de las tarjetas, y hacer mute durante el inicio.
#
# - "pulse_manager" gestiona Pulseadio para poder usar Jack.
#
# - En el arranque de Jack se detecta si existiera Pulseaudio.
#
# - Se incorpora Ecasound (opcional) para la función PEQ (Paremetric EQ)
#
# - Al objeto de optimizar las esperas manuales tras el arranque de
#   jackd, brutefir, ecasound, mpd y controlserver se sustituye
#   time(command_delay) por un bucle de comprobación de cada proceso.
#
# - Recupera el último preset o el preset por defecto (opcional en audio/config)
#
# - Se añade información del PEQ al final del arranque (if load_ecasound)
#
# - En lugar de getstatus, se usa una instancia ConfigParser para poder
# leer el estado del FIRtro también al finalizar este script.
#
# v2.1
#
# - Se reescriben los niveles de ejecución.
#
# - Ecasound se inicia a la Fs del sistema.
#
# - Se usa el path completo ~/lspk/altavoz/FS/brutefir_config
#   como argumento de arranque de brutefir.
#
# v2.2a
# - Se adapta la sección de arranque de mplayer a los puertos brutefir/ecasound
# - se incorpora jacktrip
#
# v2.2b
# - Se permite zita o alsa_in/out para resampling de tarjetas externas (audio/config, soundcards.py)
#--------------------------------------------------------------------------------------

import sys
# para poder importar los módulos del FIRtro locales en ~/bin:
sys.path.append('/home/firtro/bin')

import os
import time
import client
import stopfirtro
from getconfig import *
#from getstatus import * # v2.0 sustituido por ConfigParser
from subprocess import check_output, Popen
import soundcards as sc
import pulse_manager as pulse

from ConfigParser import ConfigParser
st = ConfigParser()
statusFile = "/home/firtro/audio/" + status_filename
def read_status():
    global input_name, filter_type, drc_eq, peq, fs, preset
    st.read(statusFile)
    input_name  = st.get("inputs",  "input")
    filter_type = st.get("general", "filter_type")
    drc_eq      = st.get("general", "drc_eq")
    peq         = st.get("general", "peq")
    fs          = st.get("general", "fs")
    preset      = st.get("general", "preset")

# INICIO:

# Opcional: DEPURACION A FICHERO:
#sys.stdout = open("/home/firtro/firtro_debug.log", "w")

original_stdout = sys.stdout
# se usa para evitar algunos printados más abajo
fnull = open(os.devnull, 'w')

read_status()   # v2.0 en sustitución de getstatus por ser estático.
audio_folder = loudspeaker_folder + loudspeaker + "/" + fs + "/"
if load_ecasound:
    firtro_ports = ecasound_ports
else:
    firtro_ports = brutefir_ports

# Cambiamos al directorio de brutefir config
# (es innecesario si se usan path completos en brutefir_config)
os.chdir(audio_folder)

def main(run_level):

    if run_level in ["audio", "core", "all"]:

        # STOPFIRTRO: paramos los procesos
        print "(initfirtro) Deteniendo procesos..."
        stopfirtro.main(run_level)
        time.sleep(command_delay)

        # Digamos a PULSEAUDIO que deje de usar cualquier tarjeta:
        if pulse.pulse_detected():
            pulse.release_all_cards()

        # recuperamos la configuracion ALSA de las tarjetas,
        # por si se hubiera tocado accidentalmente  el alsamixer...
        print "(initfirtro) Recuperando ALSA mixer de las tarjetas..."
        sc.alsa_restore_cards()

        # despues de restaurar los ajustes ALSA de la(s) tarjeta(s)
        # muteamos la tarjeta principal para evitar subidones sorpresa
        # antes de cargar el estado anterior
        print "(initfirtro) haciendo MUTE en la tarjeta del sistema"
        sc.alsa_mute_system_card("on")

        # Cargamos el nucleo básico de audio

        # JACK (v2.0)
        print "(initfirtro) Arrancando JACK ..."
        jack_cmd_list = [jack_path] + jack_options.split() + ["-r" + fs]
        if "alsa" in jack_options:
            jack_cmd_list += ["-d" + system_card]
        elif not "dummy" in jack_options:
            print "(initfirtro.py) Error arrancando JACK: backend desconocido"
            sys.exit(-1)
        if not pulse.pulse_detected():
            # VERSION "BLACK BOX":
            jack = Popen(jack_cmd_list, stdout=None, stderr=None)
        else:
            # VERSION DESKTOP con Pulseaudio:
            # suspendemos PULSEAUDIO sobre ALSA en favor de JACK:
            jack = Popen(["pasuspender", "--"] + jack_cmd_list, stdout=None, stderr=None)
        # esperamos a jackd:
        intentos = 32 # * 0.25 = 8 segundos
        while intentos:
            try:
                if "system" in check_output("jack_lsp", shell=True):
                    print "(initfirtro.py) Ha arrancado JACK."
                    break
            except:
                pass
            intentos -=1
            time.sleep(.25)
        if not intentos:
            print "(initfirtro.py) Error arrancando JACK"
            sys.exit(-1)
        time.sleep(command_delay) # esperamos un poco más ...

        if pulse.pulse_detected():
            # conectamos PULSEAUDIO con JACK (puerto pulse_sink en jack)
            pulse.pulse2jack()
            # incluimos el módulo rtp receiver
            pulse.rtp_receiver()
            # seguimos si pulse esta ya en jack:
            intentos = 4
            while intentos:
                if "pulse_sink" in check_output("jack_lsp", shell=True):
                    break
                intentos -=1
                time.sleep(.25)

        # Inicializaremos los posibles monitores externos de señal del FIRtro
        # Conectamos a JACK tarjetas adicionales mediante resampling (zita-j2a/alsa_out)
        # (mediante el modulo soundcards aka sc)
        for card in system_card.split() + external_cards.split():
            # bareCard devuelve el nombre de la tarjeta sin "hw:" y sin el device ",X"
            if [x for x in jack_external_monitors.split() if sc.bareCard(card) in x]:
                print "(initfirtro) Arrancando RESAMPLER en " + card + " ..."
                if "alsa" in resampler:
                    sc.arranca_resampler(card, fs, "alsa_out")
                elif "zita" in resampler:
                    sc.arranca_resampler(card, fs, "zita-j2a")
                else:
                    print "(initfirtro) (!) Revisar resampler en audio/config."

        # Brutefir
        print "(initfirtro) Arrancando BRUTEFIR ..."
        import brutefir_cli
        bf_config_path = audio_folder  + "brutefir_config"
        bf_params = brutefir_options.replace("brutefir_config", "") + " " + bf_config_path
        brutefir = Popen([brutefir_path] + [bf_params] , stdout=None, stderr=None)
        t = 0
        while t < 10:
            time.sleep(command_delay)
            try: # este try es porque puede haber un error de socket
                if brutefir_cli.bfcli("quit"):
                    print "(initfirtro) Ha arrancado BRUTEFIR."
                    break
            except:
                print "(initfirtro) ... esperando a BRUTEFIR...."
            t += 1
        time.sleep(command_delay) # de cortesía para que esté disponible en jack

        if load_ecasound:
            # --- Ecasound (v2.1)
            import peq_control
            print "(initfirtro) Arrancando ECASOUND ..."
            ecsFile = config_folder + "PEQx" + ecasound_filters + "_defeat_" + format(fs) + ".ecs"
            if not os.path.exists(ecsFile):
                print "(initfirtro) Revisar ecasound_filters en ~/audio/config"
                print "(initfirtro) ERROR no se localiza " + ecsFile
                sys.exit(-1)
            ecsCmd = "-q --server -s:" + ecsFile
            ecasound = Popen([ecasound_path] + ecsCmd.split(), stdout=None, stderr=None)
            t = 0
            while t < 20:
                time.sleep(.5)
                try: # este try es porque puede haber un error de socket
                    if "running" in peq_control.ecanet("engine-status"):
                        print "(initfirtro) Ha arrancado ECASOUND."
                        time.sleep(.5) # de cortesía
                        break
                except:
                    print "(initfirtro) Esperando a ECASOUND ..."
                t += 1
            if t >= 20:
                print "(initfirtro) <!> ERROR COMUNICANDO CON ECASOUND"
        else:
            print "(initfirtro) NO se carga ECASOUND."

        if run_level in ["core", "all"]:

            # mpd (v2.0)
            if load_mpd:
                print "(initfirtro) Arrancando MPD ..."
                mpd = Popen([mpd_path] + mpd_options.split(), stdout=None, stderr=None)
            # esperamos 4 segundos salvo si mpd ya hubiera arrancado:
            intentos = 16 # 16 * 0.25 = 4 segundos
            while intentos:
                try:
                    if check_output("pgrep -l mpd", shell=True):
                        print "(initfirtro) Ha arrancando MPD."
                        break
                except:
                    pass
                intentos -=1
                time.sleep(.25)
            if not intentos:
                print "(initfirtro) Error arrancando MPD."

            # Mplayer v2.2
            mplayer_ports = "jack:name=mplayer:port=" + firtro_ports.split(":")[0]
            if load_mplayer_cdda:
                tmp = cdda_options + " --ao=" + mplayer_ports
            if load_mplayer_tdt:
                tmp = tdt_options  + " --ao="  + mplayer_ports
            if load_mplayer_cdda or load_mplayer_tdt:
                print "(initfirtro) Arrancando MPLAYER ..."
                mplayer = Popen([mplayer_path] + tmp.split(), stdout=None, stderr=None)

            # Jacktrip
            if load_jacktrip:
                if "-s" in jacktrip_options:
                    jtmode = "SERVER"
                else:
                    jtmode = "CLIENT"
                print "(initfirtro) Arrancando JACKTRIP " + jtmode + " ..."
                jacktrip = Popen([jacktrip_path] + jacktrip_options.split(), stdout=None, stderr=None)
                time.sleep(command_delay)

            # Netjack
            if load_netjack:
                print "(initfirtro) Arrancando NETJACK ..."
                netjack = Popen([netjack_path] + netjack_options.split(), stdout=None, stderr=None)
                time.sleep(command_delay)

            # Shairport
            if load_shairport:
                shairport = Popen([shairport_path] + shairport_options.split(), stdout=fnull, stderr=fnull)
                time.sleep(command_delay)

            # Squeezeslave
            if load_squeezeslave:
                squeezeslave = Popen([squeezeslave_path] + squeezeslave_options.split(), stdout=None, stderr=None)
                time.sleep(command_delay)

            # Mopidy
            if load_mopidy:
                mopidy = Popen([mopidy_path] + mopidy_options.split(), stdout=None, stderr=None)
                time.sleep(command_delay)

            if run_level in ["all"]:

                # Cargamos el resto

                # Controlserver (v2.0)
                print "(initfirtro) Arrancando el SERVER ..."
                control = Popen(["python", control_path], stdout=None, stderr=None)
                # esperamos hasta 15 segundos:
                intentos = 30 # 30 * 0.5 = 15 segundos
                while intentos:
                    try:
                        if "status" in check_output("echo status|nc localhost 9999", shell=True):
                            print "(initfirtro) Ha arrancando el SERVER."
                            break
                    except:
                        pass
                    intentos -=1
                    time.sleep(.5)
                if not intentos:
                    print "(initfirtro) (i) todavía no se ha podido comunicar con el SERVER ..."

                # Lirc
                if load_irexec:
                    irexec = Popen([irexec_path] + irexec_options.split(), stdout=None, stderr=None)

                # client175
                if load_client175:
                    client175 = Popen(["python", client175_path] + client175_options.split(), stdout=fnull, stderr=fnull)
                    time.sleep(command_delay)

                # mpdlcd (MPD client for lcdproc)
                if load_mpdlcd:
                    mpdlcd = Popen([mpdlcd_path] + mpdlcd_options.split(), stdout=None, stderr=None)
                    time.sleep(command_delay)

        # Restaura el estado anterior (se supone que el server esta siempre en ejecucion)
        # Para que no salga todo el status que devuelve la funcion firtro_socket
        # primero guardamos stdout
        original_stdout = sys.stdout
        # redirigimos la salida a null
        sys.stdout = fnull
        # enviamos la orden
        client.firtro_socket("config")
        time.sleep(command_delay)
        # y restauramos stdout
        sys.stdout = original_stdout

        # Restaura las entradas
        print "(initfirtro) Recuperando INPUT ..."
        client.firtro_socket("input restore")

        # v2.0 PRESETS: recuperamos el preset al arranque del FIRtro:
        if default_preset:
            client.firtro_socket("preset " + default_preset)
            tmp = "por defecto: " + default_preset
        else:
            client.firtro_socket("preset " + preset)
            tmp = "usado por última vez: " + preset
        print "(initfirtro) recuperando el PRESET " + tmp

        # v2.0 desMuteamos la tarjeta a nivel ALSA
        print "(initfirtro) quitando MUTE en la tarjeta del sistema"
        sc.alsa_mute_system_card("off")

        # v2.0: Volvemos a leer el estado ya que hemos cargado un preset:
        read_status()

        # Alguna información
        print "\n(initfirtro):"
        print "Cargado el altavoz \"" + loudspeaker + "\" con fs=" + fs + "."
        print "Activada la entrada \"" + input_name + "\" y los filtros de tipo \"" + filter_type + "\"."
        print "La ecualización de sala (fir drc) es la número " + drc_eq + "."
        if load_ecasound:
            print "El ecualizador paramétrico es: " + peq

    else:
        print __doc__


if __name__ == "__main__":
    if sys.argv[1:]:
        run_level = sys.argv[1].lower()
    else:
        run_level = "all"
    print "(initfirtro) iniciando: " + run_level
    main(run_level)


#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    Uso:
    initfirtro.py [ audio | core | all* ]   (* por defecto)
    audio: Jack, Brutefir, Ecasound.
    core:  + Mpd y otros players, Netjack.
    all:   + Server, Lirc
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
# - Se adapta la sección de arranque de mplayer
# - se incorpora jacktrip
#
# v2.2b
# - Se permite zita o alsa_in/out para resampling de tarjetas externas (audio/config, soundcards.py)
#
# v2.2c
# - Cambios en el lanzamiento del server.
#
# v2.2d
# - Arranque de mplayer con instancias separadas para cada servicio (tdt y/o cdda)
# - Se introduce el módulo wait4 para verificar el arranque de procesos.
# - Se añade el arranque de client_mpd.py para el control de nivel ligado
#   al control de volumen de MPD usando "mixer_type null".
#
# v2.2e
# - Se usa el nuevo modulo mpdconf_adjust para reconfigurar MPD con el puerto adecuado brutefir o ecasound
# - Se revisa la gestion de canales de radio
#
# v2.2f
# - se recupera el uso de getstatus para consula
#--------------------------------------------------------------------------------------

import sys
# para poder importar los módulos del FIRtro locales en ~/bin:
sys.path.append('/home/firtro/bin')

import os
import time
import client
import stopfirtro
from getconfig import *
from getstatus import *
from subprocess import check_output, Popen, call
import soundcards as sc
import pulse_manager as pulse
import radio_channel # v2.2e
from wait4 import wait4result
import mpdconf_adjust

HOME = os.path.expanduser("~")

##########
# INICIO #
##########

# Opcional: DEPURACION A FICHERO:
#original_stdout = sys.stdout
#sys.stdout = open("/home/firtro/firtro_debug.log", "w")

# se usa para evitar algunos printados más abajo
fnull = open(os.devnull, 'w')

audio_folder = loudspeaker_folder + loudspeaker + "/" + fs + "/"

# Puertos de entrada a FIRtro:
if load_ecasound:
    firtro_ports = ecasound_ports
else:
    firtro_ports = brutefir_ports

# Cambiamos al directorio de brutefir config
# (nota: esto es innecesario si se usan path completos en brutefir_config)
os.chdir(audio_folder)

def main(run_level):

    # para controlar si el server.py está running y atiende conexiones
    serverisonline = False

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
        # Esperamos a jackd:
        if wait4result("jack_lsp", "system"):
            print "(initfirtro) Ha arrancado JACK."
        else:
            print "(initfirtro) Error arrancando JACK."
            sys.exit()

        if pulse.pulse_detected():
            # conectamos PULSEAUDIO con JACK (puerto pulse_sink en jack)
            pulse.pulse2jack()
            # incluimos el módulo rtp receiver
            pulse.rtp_receiver()
            # seguimos si pulse esta ya en jack:
            wait4result("jack_lsp", "pulse_sink")

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
        # esperamos a Brutefir
        if wait4result("echo 'quit' | nc localhost 3000", "Welcome", tmax=5, quiet=True):
            print "(initfirtro) Ha arrancado BRUTEFIR."
        else:
            print "(initfirtro) Error arrancando BRUTEFIR."
            sys.exit()

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
            # Esperamos a Ecasound:
            if wait4result("jack_lsp", "ecasound", tmax=5, quiet=True):
                print "(initfirtro) Ha arrancado ECASOUND."
            else:
                print "(initfirtro) Error arrancado ECASOUND."
                sys.exit()
        else:
            print "(initfirtro) NO se carga ECASOUND."

        if run_level in ["core", "all"]:

            # MPD (v2.2e)
            if load_mpd:

                # Antes de arrancar mpd, adecuamos destination_ports en ~/.mpdconf
                if "brutefir" in firtro_ports:
                    tmp = mpdconf_adjust.modifica_jack_destination_ports("brutefir")
                else:
                    tmp = mpdconf_adjust.modifica_jack_destination_ports("ecasound")
                if tmp:
                    print "(initfirtro) Arrancando MPD ..."
                    mpd = Popen([mpd_path] + mpd_options.split(), stdout=None, stderr=None)
                    # Aquí no es necesario esperar al arranque, lo comprobaremos más abajo para 'client_mpd.py'
                else:
                    print "(initfirtro) Error validando .mpdconf, no se lanza  MPD."
            else:
                print "(initfirtro) Está deshabilitada la carga de MPD."
                
            # Mplayer1 (Nota: MPLAYER2 ha quedado discontinued, usamos MPLAYER)
            if load_mplayer_cdda or load_mplayer_tdt:

                # Las opciones configurables por usuario en audio/config quedan reducidas a -quiet y -nolirc
                opts =  mplayer_options
                # El resto de opciones se completan aquí:
                opts += " -idle -slave"

                # Mplayer CDDA:
                if load_mplayer_cdda:
                    opts += " -profile cdda -input file=" + cdda_fifo
                    print "(initfirtro) Arrancando MPLAYER (CDDA)..."
                    mplayer = Popen([mplayer_path] + opts.split(), stdout=None, stderr=None)

                # Mplayer TDT:
                if load_mplayer_tdt:
                    opts += " -profile tdt -input file=" + tdt_fifo
                    print "(initfirtro) Arrancando MPLAYER (TDT)..."
                    mplayer = Popen([mplayer_path] + opts.split(), stdout=None, stderr=None)
                    # resintoniza la última emisora indicada en el archivo de estado (v2.2e)
                    if radio_channel.select_preset(radio):
                        print "(initfirtro) Resintonizando TDT presintonía: " + radio
                    else:
                        print "(initfirtro) (i) ERROR resintonizando TDT presintonía: " + radio
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

                # Controlserver (v2.2c)
                print "(initfirtro) Arrancando el SERVER ..."
                control = Popen(["python", control_path], stdout=None, stderr=None)
                # Esperamos hasta 10 segundos para máquinas lentas
                segundos = 10
                while segundos > 0:
                    try:
                        # OjO debemos usar "close" para terminar la conexión:
                        client.firtro_socket("close")
                        serverisonline = True
                        break
                    except:
                        pass
                    segundos -= 1
                    time.sleep(1)
                if segundos > 0:
                    print "(initfirtro) Ha arrancado el SERVER."
                else:
                    print "(initfirtro) Inicio interrumpido: el SERVER no está accesible :-/"
                    sys.exit() # INTERRUMPIMOS INITFIRTRO

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

        # NOTA: arriba hemos comprobado que el server esté en ejecucion.

        # Restaura el estado anterior
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

        # v2.0d Opción de TONE DEFEAT
        if tone_defeat_on_startup:
            client.firtro_socket("bass 0")
            client.firtro_socket("treble 0")

        # v2.0 PRESETS: recuperamos el preset por DEFECTO (si estuviera declarado)
        if default_preset:
            client.firtro_socket("preset " + default_preset)
            # nos ponemos al dia de los efectos del preset 
            status.readfp(statusfile)

        # v2.0 desMuteamos la tarjeta a nivel ALSA
        print "(initfirtro) quitando MUTE en la tarjeta del sistema"
        sc.alsa_mute_system_card("off")

        # V2.0 enlace con el control de volumen ficticio de MPD
        if mpd_volume_linked2firtro and load_mpd:
            print "(initfirtro) Esperando a MPD ... (10 seg)"
            if wait4result("pgrep -l mpd", "mpd", tmax=10, quiet=True):
                print "(initfirtro) Ha arrancado MPD."
                print "(initfirtro) Arrancando CLIENT_MPD ..."
                control = Popen(["python",  "/home/firtro/bin/client_mpd.py"], stdout=None, stderr=None)
            else:
                print "(initfirtro) Error detectando MPD, no se inicia CLIENT_MPD"

        # Restaura las entradas
        # v2.0d: Antes de recuperar la entrada de status, en caso de ser algun player
        # conviene cerciorarse de que el player haya arrancado para que la conexión sea efectiva.
        if "mpd" in input_name:
            wait4result("jack_lsp", "mpd", tmax=5)
        if "tdt" in input_name or "cdda" in input_name:
            wait4result("jack_lsp", "mplayer", tmax=5)
        print "(initfirtro) Recuperando INPUT ..."
        client.firtro_socket("input restore")
        
        # Alguna información
        print "\n(initfirtro):"
        if tone_defeat_on_startup:
            print "Se ha aplicado TONE DEFEAT." 
        if default_preset:
            print "Se ha cargado el PRESET por DEFECTO: " + preset
        else:
            print "Se ha recuperado el PRESET: " + preset
        print "Cargado el ALTAVOZ \"" + loudspeaker + "\" con FS=" + fs + "."
        print "Activada la ENTRADA \"" + input_name + "\" y los FILTROS de tipo \"" + filter_type + "\"."
        print "La ecualización de sala (DRC FIR) es la número " + drc_eq + "."
        if load_ecasound:
            print "El ecualizador paramétrico PEQ es: " + peq

    else:
        print __doc__


if __name__ == "__main__":
    if sys.argv[1:]:
        run_level = sys.argv[1].lower()
    else:
        run_level = "all"
    print "(initfirtro) iniciando: " + run_level
    main(run_level)

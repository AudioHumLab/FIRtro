#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    'initfirtro.py' rearranca el server y los módulos de FIRtro.

    Uso:

    initfirtro.py [ core | audio | core+players | all ]   (por defecto 'all')

    core o audio:   Jack, Brutefir, Ecasound.
    core+players:   + MPD y otros players
    all:            + control por Lirc y algunos clients para display
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
#   sleep(command_delay) por un bucle de comprobación de cada proceso.
#
# - Recupera el último preset o el preset por defecto (opcional en audio/config)
#
# - Se añade información del PEQ al final del arranque (if load_ecasound)
#
# v2.1
#
# - Se reescriben los niveles de ejecución: core, core+players, all
#
# - Ecasound se inicia a la Fs del sistema.
#
# - Se usa el path completo ~/lspk/altavoz/FS/brutefir_config
#   como argumento de arranque de brutefir.
#
# v2.2a
# - Se adapta la sección de arranque de mplayer
# - Se incorpora jacktrip
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
#
# v2.2f
# - Se recupera el uso de getstatus para consulta dinámica
# - El server se arranca inmediatemante despues del nucleo del audio (jack+brutefir)
#   para levantar los puertos dummy en jack que serán usados por MPD.
# - Se deja de gestionar aquí el pausado de los players integrados.
#     - Nueva opción de volumen predefinido al arranque
#
# v2.2g
# - Se añade spotifymonitor y mpdmonitor para informar a los servidores de display
# - OJO los servidores de display arrancan justo después de stopfirtro para
#   que estén disponibles para el server.py
#
# v2.2h
# - Se reubica el chequeo de server accesible
# - Se incorpora zita-njbridge (cable de audio por la red)
#
# v2.2i
# - Reordenacion del código, más comentado.
# - Nuevos alias run_level
# - Funcion auxiliar lee_status para leer audio/status al vuelo,
#   en lugar de getstatus estático.
#--------------------------------------------------------------------------------------

import os
import sys
from time import sleep
import client
import stopfirtro
from getconfig import *
from subprocess import Popen
import soundcards as sc
import pulse_manager as pulse
from wait4 import wait4result
import mpdconf_adjust

HOME = os.path.expanduser("~")

# FUNC.AUX v2.2i Lee audio/status al vuelo
def lee_status():
    f = open("/home/firtro/audio/status", "r")
    lineas = f.read().split("\n")
    f.close()
    dicci = {}
    for linea in lineas:
        if not [x for x in linea if x in ('#', ';', '[')]:
            if "=" in linea:
                linea = linea.split("=")
                linea = [x.strip() for x in linea]
                param = linea[0]
                valor = linea[1]
                dicci[param] = valor
    return dicci

# FUNC.AUX Para limitar el volumen según lo configurado opcionalmente en audio/config
def limit_level(level_on_startup, max_level_on_startup):
    if max_level_on_startup:
        max_level_on_startup = float(max_level_on_startup)
    else:
        max_level_on_startup = 0.00

    # Si se especifica nivel un fijo al arranque...
    if level_on_startup:
        level_on_startup = float(level_on_startup)
        # ... aún así le aplicaremos el límite:
        newlevel = min(level_on_startup, max_level_on_startup)
        client.firtro_socket("level " + str(newlevel))

    # si no se pide nivel fijo
    else:
        if lee_status()['level'] > max_level_on_startup:
            client.firtro_socket("level " + str(max_level_on_startup))

def main(run_level):

    # 1 # PRELIMINARES

    # 1.1 # STOPFIRTRO parada de procesos
    print "(initfirtro) Deteniendo procesos..."
    stopfirtro.main(run_level)

    # 1.2 # DISPLAY SERVERS (v2.2g)
    # LCD_server
    #   OjO normalmente el daemon LCDd no se carga aquí, suele ser un servicio del sistema
    if load_LCD_server:
        print "(initfirtro) Arrancando LCD_server ..."
        Popen([LCD_server_path, LCD_server_options] , stdout=None, stderr=None)
    # INFOFIFO_server (vuelca a una fifo el estado de FIRtro y del PLAYER de la entrada)
    if load_INFOFIFO_server:
        print "(initfirtro) Arrancando INFOFIFO_server ..."
        Popen([INFOFIFO_server_path,INFOFIFO_server_options] , stdout=None, stderr=None)

    # 1.3 # PULSEAUDIO debe dejar de usar cualquier tarjeta:
    if pulse.pulse_detected():
        pulse.release_all_cards()

    # 1.4 # Recuperamos la configuracion ALSA de las TARJETAS DE SONIDO
    #     por si se hubiera tocado accidentalmente el alsamixer.
    print "(initfirtro) Recuperando ALSA mixer de las tarjetas..."
    sc.alsa_restore_cards()

    # 1.5 # MUTEAMOS la tarjeta principal para evitar subidones sorpresa
    #     antes de cargar el estado anterior
    print "(initfirtro) haciendo MUTE en la tarjeta del sistema"
    sc.alsa_mute_system_card("on")

    # 2 # CARGA EL NUCLEO BÁSICO DE AUDIO (Jack, Brutefir, Ecasound)

    # 2.1 # JACK
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

    # Pulseaudio en JACK:
    if pulse.pulse_detected():
        # conectamos PULSEAUDIO con JACK (puerto pulse_sink en jack)
        pulse.pulse2jack()
        # incluimos el módulo rtp receiver
        pulse.rtp_receiver()
        # seguimos si pulse está ya presente en jack:
        wait4result("jack_lsp", "pulse_sink")

    # MONITORES de señal
    # Añadimos en JACK las tarjetas 'externas' (adicionales resampleadas)
    # que queremos usar como monitores externos de señal del FIRtro.
    # Para ello usamos el módulo soundcards aka 'sc'.
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

    # CABLES DE AUDIO POR LA RED opcionales:
    # Jacktrip
    if load_jacktrip:
        if "-s" in jacktrip_options:
            jtmode = "SERVER"
        else:
            jtmode = "CLIENT"
        print "(initfirtro) Arrancando JACKTRIP " + jtmode + " ..."
        jacktrip = Popen([jacktrip_path] + jacktrip_options.split(), stdout=None, stderr=None)
        sleep(command_delay)

    # Netjack
    if load_netjack:
        print "(initfirtro) Arrancando NETJACK ..."
        netjack = Popen([netjack_path] + netjack_options.split(), stdout=None, stderr=None)
        sleep(command_delay)

    # Zita-njbridge
    if load_zita_j2n:
        print "(initfirtro) Arrancando ZITA-Jack2Net ..."
        Popen([zita_j2n_path] + zita_j2n_options.split(), stdout=None, stderr=None)
        sleep(command_delay)
    if load_zita_n2j:
        print "(initfirtro) Arrancando ZITA-Net2Jack ..."
        Popen([zita_n2j_path] + zita_n2j_options.split(), stdout=None, stderr=None)
        sleep(command_delay)

    # 2.2 # BRUTEFIR
    print "(initfirtro) Arrancando BRUTEFIR ..."
    import brutefir_cli
    tmp = brutefir_path + " " + audio_folder + "brutefir_config " + brutefir_options
    Popen(tmp, shell=True)
    # Esperamos a Brutefir
    if wait4result("echo 'quit' | nc localhost 3000", "Welcome", tmax=5, quiet=True):
        print "(initfirtro) Ha arrancado BRUTEFIR."
    else:
        print "(initfirtro) Error arrancando BRUTEFIR."
        sys.exit()

    # 2.3 # ECASOUND
    if load_ecasound:
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

    # 3 # SERVER
    # ver notas v2.2f
    print "(initfirtro) Arrancando el SERVER ..."
    control = Popen(["python", control_path], stdout=None, stderr=None)

    # 4 # PLAYERS INTEGRADOS EN FIRtro
    if run_level in ["core+players", "all"]:

        # MPD (v2.2e)
        if load_mpd:

            # Antes de arrancar mpd, adecuamos destination_ports en ~/.mpdconf
            if mpdconf_adjust.modifica_jack_destination_ports("dummy"):
                print "(initfirtro) Arrancando MPD ..."
                Popen([mpd_path] + mpd_options.split(), stdout=None, stderr=None)
                # Aquí no es necesario esperar al arranque, lo comprobaremos más abajo para 'client_mpd.py'
            else:
                print "(initfirtro) Error validando .mpdconf, no se lanza  MPD."
        else:
            print "(initfirtro) Está deshabilitada la carga de MPD."

        # MPLAYER (Nota: MPLAYER2 ha quedado discontinued, usamos MPLAYER)
        if load_mplayer_cdda or load_mplayer_tdt:

            # Las opciones configurables por usuario en audio/config quedan reducidas a -quiet y -nolirc
            opts =  mplayer_options
            # El resto de opciones se completan aquí:
            opts += " -idle -slave"

            # Mplayer CDDA:
            if load_mplayer_cdda:
                opts_cdda = opts + " -profile cdda -input file=" + cdda_fifo
                print "(initfirtro) Arrancando MPLAYER (CDDA)..."
                Popen([mplayer_path] + opts_cdda.split(), stdout=None, stderr=None)

            # Mplayer TDT:
            if load_mplayer_tdt:
                opts_tdt = opts + " -profile tdt -input file=" + tdt_fifo
                print "(initfirtro) Arrancando MPLAYER (TDT)..."
                Popen([mplayer_path] + opts_tdt.split(), stdout=None, stderr=None)

        # Shairport
        if load_shairport:
            shairport = Popen([shairport_path] + shairport_options.split(), stdout=fnull, stderr=fnull)
            sleep(command_delay)

        # Squeezeslave
        if load_squeezeslave:
            squeezeslave = Popen([squeezeslave_path] + squeezeslave_options.split(), stdout=None, stderr=None)
            sleep(command_delay)

        # Mopidy
        if load_mopidy:
            mopidy = Popen([mopidy_path] + mopidy_options.split(), stdout=None, stderr=None)
            sleep(command_delay)

    # 5 # RESTO DE FUNCIONES 'all'
    if run_level in ["all"]:

        # CONTROL FRIKI de FIRtro mediante IR (LIRC)
        if load_irexec:
            irexec = Popen([irexec_path] + irexec_options.split(), stdout=None, stderr=None)

        # Clientes de los DISPLAY servers
        # mpdlcd (MPD client for lcdproc)
        if load_mpdlcd:
            mpdlcd = Popen([mpdlcd_path] + mpdlcd_options.split(), stdout=None, stderr=None)
        # v2.2g spotifymonitor (monitor SPOTIFY para los displays de FIRtro)
        if load_spotifymonitor:
            print "(initfirtro) Arrancando SPOTIFYMONITOR ..."
            Popen([spotifymonitor_path] + spotifymonitor_options.split(), stdout=None, stderr=None)
        # v2.2g mpdmonitor (monitor MPD para los displays de FIRtro)
        if load_mpdmonitor:
            print "(initfirtro) Arrancando MPDMONITOR ..."
            Popen([mpdmonitor_path] + mpdmonitor_options.split(), stdout=None, stderr=None)

    # 6 # Esperamos al SERVER para máquinas lentas (v2.2h)
    segundos = 20
    while segundos:
        print "(initfirtro) Esperando al SERVER ("+ str(20-segundos) + "s) " + "." * segundos
        try:
            # OjO debemos usar "close" para terminar la conexión:
            client.firtro_socket("close")
            break
        except:
            pass
        segundos -= 1
        sleep(1.0)
    if segundos:
        print "(initfirtro) Ha arrancado el SERVER :-)"
    else:
        print "(initfirtro) Inicio interrumpido: el SERVER no está accesible. Bye :-/"
        sys.exit() # INTERRUMPIMOS INITFIRTRO

    # 7 # RECUPERAMOS LOS AJUSTES de FIRtro

    # Nota: Redirigimos stdout a /dev/null Para que no salga todo
    #       el chorizo  que devuelve la funcion firtro_socket
    original_stdout = sys.stdout
    sys.stdout = fnull
    client.firtro_socket("config")  # el comando 'config' restaura los valores guardados en audio/status
    sys.stdout = original_stdout

    # 7.1 # TONE DEFEAT
    if tone_defeat_on_startup:
        client.firtro_socket("bass 0")
        client.firtro_socket("treble 0")

    # 7.2 # PRESET por DEFECTO
    preset = lee_status()['preset']
    if default_preset:
        client.firtro_socket("preset " + default_preset)
    else:
        client.firtro_socket("preset " + preset)

    # 7.3 # Actualizamos el ESTADO audio/status con los efectos del preset
    estado = lee_status()

    # 7.4 # LIMITE DE VOLUMEN opcional al arranque
    limit_level(level_on_startup, max_level_on_startup)

    # 7.5 # VOLUME LINKED to MPD (opcional)
    #       NOTA: no es compatible con Pulseaudio, ver doc/dev/MPD_volume2FIRtro.md
    if mpd_volume_linked2firtro and load_mpd:
        if not pulse.pulse_detected():
            print "(initfirtro) Esperando a MPD ..."
            if wait4result("pgrep -l mpd", "mpd", tmax=10, quiet=True):
                print "(initfirtro) Ha arrancado MPD."
                Popen(["mpc", "enable", "alsa_dummy"], stdout=None, stderr=None)
                print "(initfirtro) Arrancando CLIENT_MPD ..."
                Popen(["python",  "/home/firtro/bin/client_mpd.py"], stdout=None, stderr=None)
            else:
                print "(initfirtro) Error detectando MPD, no se inicia CLIENT_MPD"
        else:
            Popen(["mpc", "disable", "alsa_dummy"], stdout=None, stderr=None)
            print "(initfirtro) 'mpd_volume_linked2firtro' NO es compatible con Pulseaudio"

    # 7.6 # RESTAURA LAS ENTRADAS
    print "(initfirtro) Recuperando INPUT: " + estado['input']
    client.firtro_socket("input restore")

    # 7.7 # DESMUTEAMOS la tarjeta de sonido a nivel ALSA
    print "(initfirtro) quitando MUTE en la tarjeta del sistema"
    sc.alsa_mute_system_card("off")

    # 8 # PRINTA ALGUNA INFORMACIÓN:
    print "(initfirtro):"
    if tone_defeat_on_startup:
        print "             Se ha aplicado TONE DEFEAT."
    print "             Altavoz:   " + loudspeaker + " (fs: " + estado['fs'] + ", xover: " + estado['filter_type'] + ")"
    print "             DRC_fir:   " + estado['drc_eq']
    if load_ecasound:
        print "             PEQ:       " + estado['peq']
    if preset:
        if default_preset:
            print "             Preset:    " + estado['preset'] + "(defeault)"
        else:
            print "             Preset:    " + estado['preset']
    print "             Input:     " + estado['input']

if __name__ == "__main__":

    # DEBUG para ver este proceso en un log
    #original_stdout = sys.stdout
    #sys.stdout = open("/home/firtro/firtro_debug.log", "w")

    # Se usa para evitar que algunos procesos auxiliares Popen
    # printen sus mensajes por esta misma terminal.
    fnull = open(os.devnull, 'w')

    fs = lee_status()['fs']
    audio_folder = loudspeaker_folder + loudspeaker + "/" + fs + "/"

    # Puertos de entrada a FIRtro:
    if load_ecasound:
        firtro_ports = ecasound_ports
    else:
        firtro_ports = brutefir_ports

    # Cambiamos al directorio de ejecución de Brutefir para que carge los coeff.
    # (nota: esto es innecesario si se usan path completos en brutefir_config)
    os.chdir(audio_folder)

    run_level = "all"
    if sys.argv[1:]:
        run_level = sys.argv[1].lower()

    if run_level == "audio": # alias
        run_level = "core"

    if run_level in ["core", "core+players", "all"]:
        print "(initfirtro) iniciando: " + run_level
        main(run_level)
    else:
        print __doc__

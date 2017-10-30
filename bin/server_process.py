#!/usr/bin/env python
#coding=utf-8
# from __future__ import with_statement # This isn't required in Python 2.6
"""
    Modulo core de FIRtro
"""
#----------------------------------------------------------------------
# v2.0a (2016-oct)
#
# - (a) Se reincorpora la funcionalidad clock :-|
#
# - Se etiquetan los printados con (server_process) para identificar el
# origen del mensaje (pendiente de adaptar niveles de verbose...)
#
# - Se comenta este código con lo afectado por la funcionalidades nuevas:
# <PRESETS>  <MONO>  <ECASOUND>
#
# - Se trabaja con firtro_ports, que tomará el valor brutefir_ports
# ó ecasound_ports si se opta por Ecasound en audio/config.
#
# - Se advierte si un un preset solicita un peq pero no se ha optado
# por cargar Ecasound
#
# v2.0b (2017-abr)
#
# - Se admite RoomGain positivo, se baja el volumen si se quiere reactivar sin headroom.
# - Se revisa el código de gestión de pcms para DRC al final de este módulo.
# - Se integra la gráfica de los paramétricos ecasound en las gráficas de la web.
# - Se revisan los comentarios de este módulo.
#
# v2.0c (2017-may)
#
# - Se enlaza con el volumen ficitio de MPD. Se incorpora un temporizador para
#   evitar atender el innecesario, por ser repetido, aunque inocuo, cambio de 'gain'
#   que llegará desde MPD después de ejecutar aquí un ajuste de 'level'.
# - Se separa la función 'firtroData' (antes 'fdata') que formatea en json
#   la información de FIRtro que se facilita a la página web de control.
#
# v2.0d (2017-ago,sep)
# - Debian 9.1: se asegura type integer en los índices de las arrays de tonos y loudness
# - Levanta puertos dummy en jack para ser usados por ej por MPD
# - Se pone write_status=False en la orden 'input restore'
#
# v.2.0e
# - Se añade comando radio_channel para pasar a gestionar aquí la radio tdt,
#   de manera que server.py conozca los cambios de canal.
# - Se admite 'radio_channel next|prev' para rotar sobre los presets del archivo audio/radio,
#   y 'radio_channel recall' para recuperar el último preset escuchado (radio_prev).
# - 'exec' acepta argumentos con el ejecutable.
#
#----------------------------------------------------------------------

import time
import ConfigParser
import socket
import sys
import json
import server_input
from basepaths import *
from getconfig import *
from getstatus import *
from getspeaker import *        # OjO tomarermos system_eq del archivo de configuración 'speaker'
from getinputs import inputs
from subprocess import Popen
from math import copysign
import numpy as np
from scipy import signal

################################################################
# (i) FIRtro 2.0 EN ADELANTE SE DESTACAN LAS LINEAS AFECTADAS  #
################################################################
import soundcards
import wait4
import presets                  ## <PRESETS>
import monostereo               ## <MONO> Funcionalidad mono/stereo.
import peq_control              ## <PEQ>  Ecasound como ecualizador paramétrico, cargado
                                ##        en modo server tcp/ip en el arranque (initfirtro.py).
import peq2fr                   ##        Módulo auxiliar para procesar archivos de EQs paramétricos.
import jack_dummy_ports         ## Levanta puertos dummy en jack para ser usados por ej MPD. Solo esta línea.
import radio_channel            ## gestion de radio_channels.py centralizada para que el server conozca los cammbios.
if mpd_volume_linked2firtro:    ## <MPD>  Control de volumen enlazado con MPD.
    import client_mpd
MPD_GAIN_FWD_TIMER = .2         ## <MPD>  Temporizador que elude la orden 'gain' que llega de MPD
                                ##        despueś de ejecutar aquí un ajuste de 'level'.

##########################################################
# Comprueba que exista el directorio de una Fs requerida #
##########################################################
def check_fs_directory(fs):
    fsPath = loudspeaker_folder + loudspeaker + "/" + format(fs)
    if os.path.exists(fsPath):
        return True
    else:
        print "(server_process) Directory not found: " + fsPath
        return False

#########################################
# Funcion para comunicarse con Brutefir #
#########################################
def bf_cli (orden):
    global warnings
    try:
        s = socket.socket()
        s.connect((bfcli_address, bfcli_port))
        s.send(orden + '; quit\n')
        s.close()
    except socket.error, (value, msg):
        s.close()
        error = "Brutefir: " +"[Errno " + str(value) +"] " + msg
        if error not in warnings: 
            warnings.append (error)

#############################################################
# Funcion para obtener la fft de los pcm DRC                #
# Se mapea sobre el array 'freq' de la etapa EQ de Brutefir #
#############################################################
def pcm_fft (freq, fs, pcm_file, window_m=0):
    # Array que contendrá el fft simplificado para las frecuencias especificadas
    fft_mag = np.zeros(len(freq))
    # Abrimos el fichero en modo binario
    try:
        fd = open(pcm_file, 'rb')
        pcm = np.fromfile(file=fd, dtype='float32')
        fd.close()
    except:
        print "(server_process) ERROR: no se puede leer " + pcm_file
        return fft_mag

    if (window_m <> 0):
        # Enventanado
        w = np.blackman(window_m * 2)
        # Nos quedamos con la parte derecha
        w = w[np.argmax(w):]
        pcm = pcm[0:len(w)] * w

    # Hacemos una fft y nos quedamos con la mitad, ya que la FFT es simétrica
    #fft = np.fft.fft(pcm)
    #m = fft.size
    #if (m % 2 == 0):
    #    fft = fft[0:m/2] #m par
    #else:
    #    fft = fft[0:((m-1)/2)+1] #m impar
    #m = fft.size

    # O hacemos directamente un rfft, que devuelve solamente las frecuencias positivas.
    # Ojo hay 1 muestra de diferencia.
    fft_data = np.fft.rfft(pcm)

    # Longitud de la fft
    m = fft_data.size

    # Convertimos a dB la parte absoluta
    fft_data = 20 * np.log10(np.abs(fft_data))

    # Obtenemos las frecuencias en Hz. Tres metodos:
    # Esto da solo freq positivas, para la longitud especificada
    fft_freq = np.linspace(0, fs/2.0, m)
    # Esto da freq positivas y negativas correspondientes a una fft, hay que dividir el resultado:
    #fft_freq = np.fft.fftfreq(len(pcm),1./fs)
    # Esto solo da las positivas, correspondietes a una rfft de la señal pcm:
    #fft_freq = np.fft.rfftfreq(len(pcm),1./fs)

    # Ahora buscamos los valores para las frecuencias especificadas
    for i in range(len(freq)):
        for j in range(len(fft_data)):
            if freq[i]-fft_freq[j] < 0:
                fft_mag[i] = fft_data[j-1]
                break
    #return [round(float(data),2) for data in fft_mag_i.tolist()]
    return fft_mag

#############################################################
# Funcion para obtener la FR de un EQ paramétrico           #
# Se mapea sobre el array 'freq' de la etapa EQ de Brutefir #
#############################################################
def peq2mag_i (peqFile, channel):
    Fs = int(fs)
    mag_i = np.zeros(len(freq))

    # Filtros paramétricos (frec, BWoct, gain):
    peqs = peq2fr.leePEQ_canal(peqFile, channel)
    # Array con la respuesta en frecuencia [(w, h), ...] de cada filtro paramétrico:
    FRs  = peq2fr.peqBW_2_fr(Fs, peqs)
    # respuesta combinada de todos los paramétricos (w, h):
    w, h = peq2fr.frSum(Fs, FRs)
    # en dBs:
    hdB = 20 * np.log10(np.abs(h))

    # Ahora queda trasladar la respuesta (calculada con Fs) a los 63
    # valores de frecuencia 'freq' de la etapa EQ y manejados en las gráficas de la web.
    f = w * Fs/(2*np.pi)    # Traducimos las w normalizadas a frecuencias reales.
    # Y usamos el algoritmo de Alberto (ver función pcm_ftt) para completar los 63 valores:
    for i in range(len(freq)):
        for j in range(len(hdB)):
            if freq[i]-f[j] < 0:
                mag_i[i] = hdB[j-1]
                break

    return mag_i

##########################################
# Funcion principal que procesar ordenes #
##########################################
def do (order):

    change_gain = False
    change_eq = False
    change_xovers = False
    change_drc = False
    change_preset = False       ## <PRESETS> ##
    change_peq = False
    change_input = False
    change_mono = False         ## <MONO> ##
    write_status = True
    # write_speaker = False     ## obsoleto (ahora system_eq se guarda temporalmente en audio/status)
    change_polarity = False
    do_mute = False
    gain_direct = False
    close = False
    quit = False
    exec_cmd = False
    exec_path = '/home/firtro/bin/'
    change_clock = False        ## v2.0a <CLOCK> recuperado de Testing3
    change_fs = False
    change_radio = False

    # Al poner este proceso en una función, las variables que estén definidas
    # en los modulos importados hay que ponerlas como globales.
    # Si no se crean como locales, OjO
    global warnings
    global gmax
    global bass
    global treble
    global loudness_ref
    global loudness_track
    global loudness_level_info
    global input_gain
    global ref_level_gain
    global gain
    global level
    global headroom
    global balance
    global system_eq
    global preset               ## <PRESETS> ##
    global peq                  ## <PEQ> ##
    global peqdefeat
    global drc_eq
    global polarity
    global filter_type
    global muted
    global input_name
    global resampled            ## posible entrada resampleada ##
    global mono, monoCompens    ## <MONO> ##
    global replaygain_track
    global loudness_level_info
    global inputs
    global control_output
    global control_clear
    global tone_mag_i
    global loudeq_mag_i
    global syseq_mag_i
    global drc_l_mag_i
    global drc_r_mag_i
    global drc2_l_mag_i
    global drc2_r_mag_i
    global drc_index
    global peq_l_mag_i          ## <PEQ> ##
    global peq_r_mag_i
    global fs                   ##
    global clock                ## <CLOCK> recuperado de Testing3 ##

    global brutefir_ports       ## v2.0 firtro_ports ##
    global ecasound_ports
    if load_ecasound:
        firtro_ports = ecasound_ports
    else:
        firtro_ports = brutefir_ports

    global last_level_change_timestamp      ## <MPD> ##
    global radio, radio_prev                # v2.0e se centraliza la gestión de la radio tdt aquí

    # Borramos los warnings
    warnings = []

    # Memorizamos los valores para poder restaurarlos
    # si no se pueden aplicar por falta de headroom
    bass_old                = bass
    treble_old              = treble
    loudness_ref_old        = loudness_ref
    loudness_track_old      = loudness_track
    loudness_level_info_old = loudness_level_info
    input_gain_old          = input_gain
    gain_old                = gain
    level_old               = level
    balance_old             = balance
    headroom_old            = headroom
    tone_mag_i_old          = tone_mag_i
    loudeq_mag_i_old        = loudeq_mag_i
    syseq_mag_i_old         = syseq_mag_i
    fs_old                  = fs            ## <CLOCK> ##
    clock_old               = clock
    preset_old              = preset        ## <PRESETS> ##
    drc_eq_old              = drc_eq
    peq_old                 = peq           ## <PEQ> ##

    # Memorizamos los parámetros de cambio de entrada por si ocurre algún error
    input_name_old = input_name
    filter_type_old = filter_type
    mono_old = mono                         ## <MONO> ##
    radio_old = radio
    radio_prev_old = radio_prev

    # Quitamos los caracteres finales
    order = order.rstrip('\r\n')
    # Separamos el comando de los argumentos
    line = order.split()
    if len(line) > 0: command = line[0]
    else: command = ""
    if len(line) > 1: arg1 = line[1]
    if len(line) > 2: arg2 = line[2]
    if len(line) > 3: arg3 = line[3]

    ## <MPD> ## v2.0c rev1 control de volumen de MPD ligado a FIRtro
    if time.time() - last_level_change_timestamp < MPD_GAIN_FWD_TIMER:
        if mpd_volume_linked2firtro:
            #print "(server_process) comando descartado: " + order + \
            #      " (reason MPD_GAIN_FWD_TIMER=" + str(MPD_GAIN_FWD_TIMER) + ")" # DEBUG
            return firtroData(locals(), globals(), inputs.sections())

    #############################################################
    # Comprueba el comando y se decide las acciones a ejecutar: #
    #                                                           #
    if control_output > 0:
        print "(server_process) Command:", order

    try:
        if command == "status":
            write_status = False

        elif command == "input":
            if len(line) > 1:
                name = arg1.lower()
                if name == "restore":
                    # Si estoy restaurando la entrada, ya la tengo en input_name
                    change_input = True
                    change_gain = True
                    change_xovers = True
                    change_eq = True
                    #muted = False
                    write_status = False
                elif name == input_name.lower():
                    # Si la entrada ya es la activa, y no estoy restaurandolas, no hago nada
                    writestatus = False
                elif inputs.has_section(name):
                    # Si la entrada existe, la memorizo y marcamos las acciones a ejecutar
                    input_name = name
                    change_input = True
                    change_xovers = True
                    change_eq = True
                    if (muted == False):
                        change_gain = True
                    else:
                        do_mute=True
                else:
                    warnings.append("Input " + name + " doesn't exit")
            else: raise

        elif command == "config":
            change_gain = True
            change_eq = True
            change_xovers = True
            change_drc = True
            change_preset = True        ## <PRESETS> ##

        elif command == "mute":
            do_mute = True
            muted = True

        elif command == "unmute":
            change_gain = True
            muted = False

        elif command == "toggle":
            muted = not(muted)
            if muted:
                do_mute = True
            else:
                change_gain = True

        elif command == "gain":
            if len(line) > 1:
                gain = float(arg1)
                change_gain = True
                gain_direct = True
            else: raise

        elif command == "gain_add":
            if len(line) > 1:
                gain += float(arg1)
                change_gain = True
                gain_direct = True
            else: raise

        elif command == "level":
            if len(line) > 1:
                level = float(arg1)
                #gain = level + ref_level_gain
                change_gain = True
            else: raise

        elif command == "level_add":
            if len(line) > 1:
                level += float(arg1)
                #gain = level + ref_level_gain
                change_gain = True
            else: raise

        elif command == "mono":       ## <MONO> ##
            if len(line) > 1:
                mono = arg1
                if mono <> mono_old:
                    change_mono = True
                    change_gain = True

        elif command == "balance":
            if len(line) > 1:
                balance = float(arg1)
                change_gain = True
            else: raise

        elif command == "xover":
            if len(line) > 1:
                filter_type = arg1
                change_eq = True
                change_xovers = True  ## <PRESETS> ##
                change_preset = True  ## ver más abajo: no hacemos nada if change_xovers, simplemente
            else: raise               ## regeneramos el preset completo con el modulo presets.py

        elif command == "drc":
            if len(line) > 1:
                if (int(arg1) <= drc_index):
                    drc_eq = arg1
                    change_drc = True
            else:
                raise

        elif command == "preset":       ## <PRESETS> ##
            if len(line) > 1:
                #preset = arg1  evitamos la restricción de hasta 3 argumentos
                preset = " ".join(line[1:])
                change_preset   = True
                change_drc      = True  ## pq los preset tienen un DRC asociado
                change_gain     = True  ## pq tb tienen ajuste de balance
                change_peq      = True  ## pq tb tienen ajuste de PEQ
            else: raise

        elif command == "peq_reload":
            change_peq = True

        elif command == "peq_defeat":
            change_peq = True

        elif command == "loudness_track":
                loudness_track = True
                change_eq = True

        elif command == "loudness_track_off":
                loudness_track = False
                change_eq = True

        elif command == "loudness_ref":
            if len(line) > 1:
                loudness_ref = float(arg1)
                change_eq = True
            else: raise

        elif command == "loudness_add":
            if len(line) > 1:
                loudness_ref += float(arg1)
                change_eq = True
            else: raise

        elif command == "treble":
            if len(line) > 1:
                treble = float(arg1)
                change_eq = True
            else: raise

        elif command == "treble_add":
            if len(line) > 1:
                treble += float(arg1)
                change_eq = True
            else: raise

        elif command == "bass":
            if len(line) > 1:
                bass = float(arg1)
                change_eq = True
            else: raise

        elif command == "bass_add":
            if len(line) > 1:
                bass += float(arg1)
                change_eq = True
            else: raise

        elif command == "polarity":
            if len(line) > 1:
                polarity = arg1
                change_polarity = True
                change_gain = True
            else: raise

        elif command == "syseq":
            system_eq = True
            change_eq = True
            # write_speaker = True  # obsoleto

        elif command == "syseq_off":
            system_eq = False
            change_eq = True
            # write_speaker = True  # obsoleto

        elif command == "exec":
            if len(line) > 1:
                # exec_arg = arg1.translate(None,'/')  # v2.0e Aceptamos argumentos del ejecutable:
                exec_arg = line[1:]
                exec_arg = " ".join([ x.translate(None,'/') for x in exec_arg])
                exec_cmd = True
            else: raise

        elif command == "clock":    # v2.0a <CLOCK> recuperado de Testing3 (y reescrito)
            if len(line) > 1:       # OjO "line" es una lista con los argumentos de la orden
                for argu in line:
                    if argu.isalpha():
                        clock = argu
                        change_clock = True
                    elif argu.isdigit():
                        fs = argu
                        change_fs = True
            else: raise
            write_status = False   # se escribirá en "if change_clok or change_fs"

        # Must be last, and override all other options
        elif command == "flat":
            system_eq = False
            loudness_track = False
            bass = 0
            treble = 0
            change_eq = True
            invert = False
            write_status = False

        elif command == "radio_channel":
            if len(line) > 1:
                new_radiopreset = arg1
                change_radio = True
                # Debido a que Mplayer desactiva momentaneamente sus puertos en jack al resintonizar,
                # activamos los mismos indicadores usados en 'input restore':
                change_input = True
                change_gain = True
                change_xovers = True
                change_eq = True
            else: raise
        # Si no se reconoce el comando
        else:
            raise

    except:
        warnings.append("Wrong command syntax")

    #                                                 #
    # Si no hubo excepciones, se pasa a la ejecución: #
    ###################################################

    ## <RADIO> ## v2.0e: Canales de radio gestionados a través del server.
    if change_radio:
        # OjO al resintonizar la TDT los puertos de Mplayer se desactivan momentaneamente,
        # por tanto esta sección se coloca al principio de la ejecución para que tengan efecto
        # los indicadores como cuando se pide un 'input restore'

        # Lista de presets definidos (descartamos los que están en blanco en audio/radio)
        lpd = [ x[0] for x in  radio_channel.channels.items('channels') if x[1] ]

        # Acondicionamos un posible argumento de texto:
        # Admitimos 'next|prev' para rotar por los presets de audio/radio:
        if new_radiopreset == "next":
            new_radiopreset = lpd[ (lpd.index(radio) + 1) % len(lpd) ]
        if new_radiopreset == "prev":
            new_radiopreset = lpd[ (lpd.index(radio) - 1) % len(lpd) ]
        # O bien, con 'recall' se recupera el último preset escuchado, es decir 'radio_prev':
        if new_radiopreset == "recall":
            new_radiopreset = radio_prev

        # Selección ordinaria de una presintonía de audio/radio:
        if radio_channel.select_preset(new_radiopreset):
            radio_prev = radio
            radio = new_radiopreset
            write_status = True
            # Esperamos a que Mplayer se desactive y vuelva a estar disponible en Jack
            time.sleep (1) # OjO importante esperar un poco a que se desactiven los puertos.
            wait4.wait4result("jack_lsp", "mplayer_tdt", tmax=8, quiet=True)
        else:
            warnings.append("Radio: el preset #" + new_radiopreset + " NO está configurado")

    ## <PRESETS> ##
    ## OjO (1/2) estos dos IF estaban justo antes del IF CHANGE_DRC (en Resto de comandos),
    ## ahora los subo aquí para que surjan efecto FILTER_TYPE, DRC, BALANCE,
    ## u otros parámetros futuros soportados en presets.ini
    if change_xovers:
        ## /// este es el código original (Resto de comandos..) que he sustituido por el modulo presets.py
        #for channel in speaker.options("out_channels"):
        #    bf_filter = '"f_' + speaker.get("out_channels", channel).split()[0] + '"'
        #    bf_coeff = '"c_' + filter_type + '-' + speaker.get("out_channels", channel).split()[1] + '"'
        #    bf_cli('cfc ' + bf_filter + ' ' + bf_coeff)
        ## \\\ ahora el cambio de xovers (filter_type = mp|lp) lo realiza el nuevo modulo "presets.py"

        # Añadimos la POSIBILIDAD de ALTERNAR el filter_type para usearse desde un botón de la web:
        if filter_type in ["cambia", "alterna", "change", "switch", "toggle"]:
            if filter_type_old == "lp": filter_type = "mp"
            else:                       filter_type = "lp"

    ## <PRESETS> ##
    ## OjO (2/2)
    if change_preset:
        # (i) OjO: los preset incluyen un DRC y BALANCE asociados, entonces
        # a la vez que configuramos el preset, obtenemos el drc y el balance que le corresponde:
        preset, drc_eq, balance, peq = presets.configura_preset(preset, filter_type)
        balance = int(balance)
        # si se hubiera pedido un preset erroneo se deja el que habia:
        if "ERROR" in preset:
            warnings += ["ERROR obteniendo el PRESET: " + preset]
            preset = preset_old
            drc_eq = drc_eq_old
            balance = balance_old
            filter_type = filter_type_old
            peq = peq_old

    ## <PEQ> ## Parametricos ECASOUND
    # Hay tres casos para tener change_peq = True
    #   1) una actualizacion de preset (comando =  preset xxxx --> peq cambia)
    #   2) se quiere una recarga del .peq actual pq ha sido editado (comando = peq_reload --> peq no cambia)
    #   3) un comando= peq_defeat --> peq cambia
    if change_peq:
        if load_ecasound:
            peqdefeat = False
            change_input = True     # para reconectar la fuente a ecasound
            if "preset" in command or "reload" in command:
                if peq <> "off":
                    PEQini = loudspeaker_folder + loudspeaker + "/" + peq + ".peq"
                    peq_control.cargaPEQini(PEQini)
                    # curvas informativas para la web:
                    peq_l_mag_i = peq2mag_i(PEQini, "left")
                    peq_r_mag_i = peq2mag_i(PEQini, "right")
                else:
                    peq_control.PEQdefeat()
                    peqdefeat = True
                    # curvas informativas para la web:
                    peq_l_mag_i = np.zeros(len(freq))
                    peq_r_mag_i = np.zeros(len(freq))
            elif "defeat" in command:
                peq_control.PEQdefeat()
                peqdefeat = True
                # curvas informativas para la web:
                peq_l_mag_i = np.zeros(len(freq))
                peq_r_mag_i = np.zeros(len(freq))
        elif not load_ecasound and peq <> "off":
            pass
            warnings += ["(!) Preset con PEQ pero ECASOUND está DESACTIVADO"]

    ## <MONO> ##
    if change_mono:
        if mono in ["toggle", "cambia", "switch", "conmuta"]:
            if mono_old == "on":
                mono = "off"
            else:
                mono = "on"
        if mono == "on":
            # hacemos el cruce de canales de entrada:
            monostereo.setMono("on")
            # COMPENSAMOS NIVELES por la mezcla de canales
            monoCompens = -6.0
        else:
            mono = "off" # corrige si se pide una opcion incorrecta
            # esto simplemente desconecta las entradas:
            monostereo.setMono("off")
            # marcamos para restaurar las entradas
            change_input = True
            # y COMPENSAMOS NIVELES
            monoCompens = +0.0

    ## v2.0a <CLOCK> no incluido en v2.0 :-|, se ha recuperado de Testing3 (OjO se ha reescrito)
    ## NOTA:    los cambios de CLOCK o de FS pueden ser:
    ##              -> explícitos en un comando "clock"
    ##              -> implícitos en un comando "input"
    if change_input:
        input_gain  = float(inputs.get(input_name, "gain"))
        input_ports =       inputs.get(input_name, "in_ports")
        filter_type =       inputs.get(input_name, "xo")
        resampled   =       inputs.get(input_name, "resampled")
        new_fs      =       inputs.get(input_name, "fs")
        new_clock   =       inputs.get(input_name, "clock")
        if not new_fs:      new_fs = fs             # apaño para audio/inputs con "fs" en blanco
        if not new_clock:   new_clock = clock       # apaño para audio/inputs con "clock" en blanco
        if new_fs != fs:
            fs = new_fs
            change_fs    = True
        if new_clock != clock:
            clock = new_clock
            change_clock = True

        if check_fs_directory(fs):
            if not change_clock and not change_fs:      # SI NO HAY CAMBIO DE Fs o de CLOCK intentamos el CAMBIO de INPUT:
                if server_input.change_input (input_name, input_ports.split(), firtro_ports.split(), resampled):
                    pass                                # El cambio de input ha ido bien.
                else:
                    warnings.append("Error changing to input " + input_name)
                    input_name      = input_name_old
                    filter_type     = filter_type_old
                    change_xovers   = False
                    change_eq       = False
                    change_gain     = False
                    write_status    = True
            else:
                pass                                    # DEJAMOS que change_clock/change_fs REINICIE el AUDIO del FIRtro
        else:
            warnings.append("Error changing to input " + input_name)
            # marcha atrás
            input_name   = input_name_old
            fs           = fs_old
            change_fs    = False
            write_status = True

        if mono == "on":                            ## <MONO> ##
            monostereo.setMono("on")                # mezcla canales de entrada (previamente se ha compensado el nivel)

    # v2.0a <CLOCK> omitido en v2.0 PRESTES :-|, se ha recuperado de Testing3 (OjO se ha reescrito)
    # - Se reconfigura el reloj de tarjetas de sonido profesionales (reloj interno/externo)
    # - Se modifica el archivo de ESTADO ~/audio/status con la nueva Fs
    # - Se reinicia el AUDIO (initfirtro.py) que leerá la nueva Fs en ~/audio/status
    if change_clock or change_fs:
        esViable = False
        if check_fs_directory(fs):                      # si hay directorio preparado con filtros para la Fs
            if soundcards.change_clock(clock, fs):      # y si el cambio en la tarjeta de sonido ha sido viable:
                    try:
                        status.set('general', 'clock', clock)
                        status.set('general', 'fs', fs) # (i) esto hará que rearranque con nueva Fs
                        statusfile = open(status_path, 'w')
                        status.write(statusfile)
                        statusfile.close()
                        esViable = True
                    except:
                        warnings.append("Failed to open status file" + status_path)
            else:
                warnings.append("Bad parameters, fs or clock")
        if esViable:    # (!!!) REINICIO del AUDIO con NUEVA Fs en ~/audio/status
            print "(server_process) REINICIANDO EL AUDIO ->>>- initfirtro.py"
            Popen(["initfirtro.py", "audio"], stdout=None, stderr=None)
        else:
            # marcha atrás
            fs           = fs_old
            clock        = clock_old
            write_status = True

    #if replaygain_track:           # revisar esto : gain o level  ¿ !!! PENDIENTE long time ago ...?
    #    gain += loudness_ref

    # Cambios de ganancia o de EQ (con control de clipping debido a input_gain y eq_mag)
    # aka "máquina de control de volumen"
    if (change_gain or change_eq):

        # Info para el potenciómetro de volumen (p.ej el slider de la web) (recálculo)
        maxlevel_i = gmax - ref_level_gain - input_gain

        # 1a) Se pide cambio de 'level' (vol. calibrado)
        if not gain_direct:
            gain = level + ref_level_gain + input_gain  # se traduce a gain.

        # 1b) o se pide un cambio de 'gain' en bruto.
        else:
            level = gain - ref_level_gain - input_gain

        # 2) Confección de la CURVA de EQ: Loudness + SysEQ (+RoomGain -HouseCurve) + Bass + Treble.
        if filter_type == no_phase_xo:
            use_phase = False
        else:
            use_phase = True
        eq_mag = np.zeros(len(freq))
        eq_pha = np.zeros(len(freq))
        tone_mag_i  = np.zeros(len(freq))
        syseq_mag_i = np.zeros(len(freq))

        if loudness_track:
            change_eq = True
            if abs(loudness_ref) > loudness_variation:
                loudness_ref = copysign(loudness_variation, loudness_ref)
            loudness_i = loudness_SPLmax - (level + loudness_SPLref + loudness_ref)
            loudness_max_i = loudness_SPLmax - loudness_SPLmin
            if loudness_i < 0:
                loudness_i = 0
            if loudness_i > loudness_max_i:
                loudness_i = loudness_max_i
            # OjO hay que asegurar que loudness_i sea un integer para evitar error al usarlo como índice del nparray
            loudness_i = int(loudness_i)
            loudeq_mag = loudness_mag_curves[:,loudness_i]
            eq_mag += loudeq_mag
            loudness_level_info = str(int(loudness_i - loudness_SPLmax + loudness_SPLref)) \
                                      + ' (' + str(round(max(loudeq_mag), 2)) + ' dB)'
            if use_phase:
                eq_pha += loudness_pha_curves[:,loudness_i]
            # Info para la web:
            loudeq_mag_i = [round(float(data),2) for data in loudness_mag_curves[:,loudness_i].tolist()]
        else:
            loudeq_mag_i = [ 0 for i in freq]

        if system_eq:
            eq_mag += syseq_mag
            syseq_mag_i += syseq_mag                # Info para la web
            if use_phase:
                eq_pha += syseq_pha

        if treble != 0:
            treble_i = tone_variation - treble
            if treble_i < 0:
                treble_i = 0
            if treble_i > 2 * tone_variation:
                treble_i = 2 * tone_variation
            treble_i = int(treble_i)                # forzarmos integer
            eq_mag += treble_mag[:,treble_i]
            if use_phase:
                eq_pha += treble_pha[:,treble_i]
            treble = tone_variation - treble_i
            tone_mag_i+= treble_mag[:,treble_i]     # Info para la web

        if bass != 0:
            bass_i = tone_variation - bass
            if bass_i < 0:
                bass_i = 0
            if bass_i > 2 * tone_variation:
                bass_i = 2 * tone_variation
            bass_i = int(bass_i)                    # forzarmos integer
            eq_mag += bass_mag[:,bass_i]
            if use_phase:
                eq_pha += bass_pha[:,bass_i]
            bass = tone_variation - bass_i
            tone_mag_i+= bass_mag[:,bass_i]         # Info para la web

        # Info para la web: ahora el tipo de datos de la variable "tone_mag_i" es numpy.ndarray,
        # demasiado complejo para enviarlo via JSON, lo convertimos en una lista tipo float.
        if isinstance(tone_mag_i, np.ndarray):
            tone_mag_i = [round(float(data), 2) for data in tone_mag_i.tolist()]

        # 3) Calculamos el HEADROOM:
        headroom = gmax - gain - np.max(eq_mag)

        # 4) Priorizamos SysEQ bajando el level si NO hubiera HEADROOM:
        if 'syseq' in command and headroom < 0:
            gain  -= np.ceil(-headroom)
            level -= np.ceil(-headroom)
            headroom = gmax - gain - max(eq_mag)    # recalculamos el headroom

        headroom = round(headroom, 2)               # para que el display no muestre "-0.0 dB"
        if headroom == -0.00: headroom = 0.00

        # 5) SI hay HEADROOM suficiente aplicamos los cambios de level y/o EQ:
        if headroom >= 0:
            if change_gain:
                gain_0 = gain + monoCompens
                gain_1 = gain + monoCompens
                if abs(balance) > balance_variation:
                    balance = copysign(balance_variation,balance)
                if balance > 0:
                    gain_0 = gain_0 - balance
                elif balance < 0:
                    gain_1 = gain_1 + balance
                if not muted:
                    bf_cli('cfia 0 0 ' + str(-gain_0) + ' ; cfia 1 1 ' + str(-gain_1))
                    # AMR 2º Entrada de brutefir (para analogica con filtros mp):
                    # bf_cli('cfia 2 2 ' + str(-gain_0) + ' ; cfia 3 3 ' + str(-gain_1))
                if not gain_direct and "level" in order and mpd_volume_linked2firtro:        ## <MPD> ##
                    # actualizamos el "falso volumen" de MPD
                    client_mpd.setvol(100 + gain)
                    last_level_change_timestamp = time.time()

            if change_eq:
                eq_str = ""
                l = len(freq)
                for i in range(l):
                    eq_str = eq_str + str(freq[i]) + '/' + str(eq_mag[i])
                    if i != l:
                        eq_str += ", "
                bf_cli('lmc eq 0 mag ' + eq_str)
                eq_str = ""
                for i in range(l):
                    eq_str = eq_str + str(freq[i]) + '/' + str(eq_pha[i])
                    if i != l:
                        eq_str += ", "
                bf_cli('lmc eq 0 phase ' + eq_str)

        # Si NO hay HEADROOM, no aplicamos los cambios, y recuperamos los valores anteriores
        else:
            warnings.append("Not enough headroom")
            bass = bass_old
            treble = treble_old
            loudness_ref = loudness_ref_old
            loudness_track = loudness_track_old
            loudness_level_info = loudness_level_info_old
            input_gain = input_gain_old
            level = level_old
            headroom = headroom_old
            gain = gain_old
            tone_mag_i = tone_mag_i_old
            loudeq_mag_i = loudeq_mag_i_old
            syseq_mag_i = syseq_mag_i_old

    ############ Resto de comandos ############
    if do_mute:
        bf_cli("cfia 0 0 m0 ; cfia 1 1 m0")
        # 2º Entrada de brutefir (para analogica con filtros mp)
        #bf_cli("cfia 2 2 m0 ; cfia 3 3 m0")

    if change_polarity:
        bf_cli('cfia 0 0 m' + polarity + '1 ; cfia 1 1 m' + polarity + '1')
        # 2º Entrada de brutefir (para analogica con filtros mp)
        #bf_cli('cfia 2 2 m' + polarity + '1 ; cfia 3 3 m' + polarity + '1')

    # (!!!) 'if change xovers' se ha pasado al inicio con la gestión de <PRESETS>
    #if change_xovers:
    #    for channel in speaker.options("out_channels"):
    #        bf_filter='"f_' + speaker.get("out_channels", channel).split()[0] + '"'
    #        bf_coeff='"c_' + filter_type + '-' + speaker.get("out_channels", channel).split()[1] + '"'
    #        bf_cli('cfc ' + bf_filter + ' ' + bf_coeff)

    if change_drc:
        # Metodo 1: Se asignan siempre coeficientes predefinidos.
        # drc0 está definido con un dirac pulse, y no tiene efecto:
        #bf_cli('cfc "f_drc_L" "c_drc' + drc_eq + '_L"; cfc "f_drc_R" "c_drc' + drc_eq + '_R"')

        # Metodo 2: Si el drc es 0, entonces se asigna el coeficiente -1,
        # optimizando latencia y uso de procesador
        if drc_eq == "0":
            bf_cli('cfc "f_drc_L" -1; cfc "f_drc_R" -1')
            # 2º Entrada de brutefir (para analogica con filtros mp)
            #bf_cli('cfc "f_drc_L2" -1; cfc "f_drc_R2" -1')
        else:
            bf_cli('cfc "f_drc_L" "c_drc' + drc_eq + '_L"; cfc "f_drc_R" "c_drc' + drc_eq + '_R"')
            # 2º Entrada de brutefir (para analogica con filtros mp)
            #bf_cli('cfc "f_drc_L2" "c_drc' + drc_eq + '_L"; cfc "f_drc_R2" "c_drc' + drc_eq + '_R"')

    # Info para la web - EQ global aplicada (drc + syseq):
    if (change_gain or change_eq or change_drc or change_peq):
        # L:
        if int(drc_eq) < len(drc_l_mag_i):
            drc2_l_mag_i = [round(float(data),2) for data in (drc_l_mag_i[int(drc_eq)] + syseq_mag_i + peq_l_mag_i).tolist()]
        else:
            drc2_l_mag_i = [round(float(data),2) for data in (syseq_mag_i + peq_l_mag_i).tolist()]
        # R:
        if int(drc_eq) < len(drc_r_mag_i):
            drc2_r_mag_i = [round(float(data),2) for data in (drc_r_mag_i[int(drc_eq)] + syseq_mag_i + peq_r_mag_i).tolist()]
        else:
            drc2_r_mag_i = [round(float(data),2) for data in (syseq_mag_i + peq_l_mag_i).tolist()]

    if exec_cmd:
        result = Popen(exec_path + exec_arg, shell=True)

    if system_eq:                                   # para no mostrar los valores
        rg_tmp = room_gain; ha_tmp = house_atten    # cuando están desactivados
    else:
        rg_tmp = ha_tmp = "0"

    if write_status:
        status.set('recording EQ', 'loudness_track', loudness_track)
        status.set('recording EQ', 'loudness_ref', loudness_ref)
        status.set('recording EQ', 'bass', bass)
        status.set('recording EQ', 'treble', treble)
        status.set('room EQ', 'drc_eq', drc_eq)
        status.set('room EQ', 'peq', peq)               ## <PEQ> ##
        status.set('room EQ', 'peqdefeat', peqdefeat)
        status.set('room EQ', 'system_eq', system_eq)
        status.set('room EQ', 'room_gain', rg_tmp)
        status.set('room EQ', 'house_atten', ha_tmp)
        status.set('level', 'level', level)
        status.set('level', 'headroom', headroom)
        status.set('level', 'balance', balance)
        status.set('general', 'polarity', polarity)
        status.set('general', 'filter_type', filter_type)
        status.set('general', 'muted', muted)
        status.set('inputs', 'input', input_name)
        status.set('inputs', 'radio', radio)
        status.set('inputs', 'radio_prev', radio_prev)
        status.set('general', 'clock', clock)           ## <CLOCK> recuperado de Testing3 ##
        status.set('general', 'fs', fs)
        status.set('inputs', 'resampled', resampled)    ## <v2.0> Entrada a través de tarjeta resampleada ##
        status.set('inputs', 'mono', mono)              ## <MONO> ##
        status.set('general', 'preset', preset)         ## <PRESETS> ##
        try:
            statusfile = open(status_path, 'w')
            status.write(statusfile)
            statusfile.close()
        except:
            warnings.append("Failed to open status file" + status_path)

    ## Se traslada este indicador al archivo de estado "status"
    ## y se deja el archivo "speaker" solo para configuracion de arranque.
    #if write_speaker:
    #    speaker.set('equalization', 'system_eq', system_eq)
    #    try:
    #        speakerfile = open(speaker_path, 'w')
    #        speaker.write(speakerfile)
    #        speakerfile.close()
    #    except:
    #        warnings.append("Failed to open speaker file" + status_path)

    # Mostramos en pantalla un resumen del estado
    if control_output > 0:
        print '----'
        print 'RefLevel gain =', ref_level_gain
        print 'Input gain    =', input_gain
        if muted:
            tmp = "(MUTED)"
        else:
            tmp = ""
        print 'Level         = ' + str(level) + '  (Gain = ' + str(gain) + ') ' + tmp
    if control_output > 1:
        print 'Headrooom     =', str(headroom) + ' dB'
        print 'Balance       =', balance
        print '----'
        if system_eq:
            print 'System EQ     =', 'Yes (' + str(round(max(syseq_mag),2)) + ' dB)'
        else:
            print 'System EQ     = off'
        print 'Room Gain     = ' + str(rg_tmp).ljust(4) + ' House Atten  = ' + str(ha_tmp)
        print 'Bass          = ' + str(bass).ljust(4)   + ' Treble       = ' + str(treble)
        if loudness_track:
            print 'Loudness      = ' + loudness_level_info + ' Loud.ref = ', loudness_ref
        else:
            print 'Loudness      = off'
        print 'PEQ           =', peq + " (defeated)" * peqdefeat
        print 'DRC           =', drc_eq
        print '---'
        print 'Filter Type   =', filter_type
        print 'Preset        =', preset
        print 'Mono          =' , mono                           ## <MONO> ##
        print 'Input         =', input_name
        print 'Fs            =', fs + ' Hz [clock = ' + str(clock) + ']' ## v2.0a recuperado <CLOCK> Testing3
        print '---'

    # Imprimimos los warnings que se hayan producido
    if len(warnings) > 0:
        print "(server_process) Warnings:"
        for warning in warnings:
            print "\t" + warning

    # A efectos de control, devolvemos un diccionario 
    # conteniendo el estado del FIRtro
    return firtroData(locals(), globals(), inputs.sections())
# ^^^^^^^^ FIN DEL do() PRINCIPAL ^^^^^^^^


# V2.0c reescritura del diccionario de estado en una función separada
def firtroData(locales, globales, entradas):
    # Obtenemos el diccionario con todas la variables y sus valores
    # Variables locales
    data = locales
    # Añadimos las variables globales
    data.update(globales)
    # Y la lista de entradas
    data.update({'inputs':entradas})
    # En esta lista almacenaremos las variables que queremos extraer del dicionario global
    keys = ['treble', 'bass', 'replaygain_track', 'level', 'maxlevel_i', 'headroom', 'muted', 'polarity',
        'fs', 'drc_eq', 'filter_type', 'clock', 'loudness_track', 'loudness_ref', 'loudness_level_info',
        'radio', 'input_name', 'input_gain', 'system_eq', 'room_gain', 'house_corner', 'house_atten',
        'ref_level_gain', 'loudspeaker', 'inputs', 'warnings', 'order','freq_i','tone_mag_i','loudeq_mag_i',
        'drc2_r_mag_i','drc2_l_mag_i','drc_index','balance','balance_variation',
        'preset', 'lista_de_presets', 'mono', 'peq', 'peqdefeat']    ## <PRESETS> <MONO> <PEQ> ##
    # Y obtenemos un nuevo diccionario filtrado, con solo las opciones que nos interesan
    fdata = { key: data[key] for key in keys}
    # Lo formateamos y lo mandamos como salida de la función
    fdata = json.dumps (fdata)
    # Devolvemos el diccionario
    return (fdata)

##################
# Inicializacion #
##################

#### <PRESETS>
lista_de_presets = presets.lista_de_presets()

#### Warnings informativos
warnings = []

#### Curvas empleadas en la etapa EQ de Brutefir
try:
    freq                = np.loadtxt(freq_path)
    loudness_mag_curves = np.loadtxt(loudness_mag_path)
    loudness_pha_curves = np.loadtxt(loudness_pha_path)
    syseq_mag           = np.loadtxt(syseq_mag_path)
    syseq_pha           = np.loadtxt(syseq_pha_path)
    treble_mag          = np.loadtxt(treble_mag_path)
    treble_pha          = np.loadtxt(treble_pha_path)
    bass_mag            = np.loadtxt(bass_mag_path)
    bass_pha            = np.loadtxt(bass_pha_path)
except:
    print "(server_process) Error: Failed to load EQ files"
    sys.exit(-1)

#### Niveles:
## <MONO> compensacion interna, no computada en el cálculo de headroom, se sumará a la gain enviada a Brutefir.
monoCompens = 0.0
if mono:
    monoCompens = -6.0
input_gain = 0
gain = level + input_gain + ref_level_gain
loudness_level_info = ""
# Info para un potenciómetro de volumen (p.ej se usará en el slider de la web)
maxlevel_i = gmax - ref_level_gain - input_gain

#### <PEQ> indicador de estado de los paramétricos forzados a cero.
peqdefeat = False

# Informacion de las frecuencias utilizadas para la etapa de EQ
freq_i = [ int(i) for i in freq]

# Inicialización de curvas informativas (xxx_i) para las gráficas de la página web.
syseq_mag_i     = np.zeros(len(freq))
drc_l_mag_i     = {}
drc_r_mag_i     = {}
drc2_l_mag_i    = [0 for i in freq] # drc2 : drc + syseq
drc2_r_mag_i    = [0 for i in freq] # drc2 : drc + syseq
tone_mag_i      = [0 for i in freq]
loudeq_mag_i    = [0 for i in freq]
peq_l_mag_i     = {}
peq_r_mag_i     = {}

### Gestión de pcms para DRC:
# (i) El diseño original en FIRtro v1.0 requiere nombres
#     de archivo pcm para drc numerados correlativamente desde 1.
#     El mecanismo de selección de DRC reserva el índice 0 para "drc plano".
drc_index = 0
drc_r_mag_i[drc_index] = np.zeros(len(freq))
drc_l_mag_i[drc_index] = np.zeros(len(freq))
# Buscamos todos los ficheros pcm de drc que existan, 
# incrementando el index y generando las curvas informativas de la web.
print "(server_process) Doing FFT of DRC pcm files..."
while True:
    # intentamos leer los pcm de drc con el siguiente índice:
    i = drc_index + 1
    tmp = loudspeaker_folder + loudspeaker + '/' +fs + "/drc-" + str(i)
    # Canal L:
    pcm_file = tmp + "-L.pcm"
    if os.path.isfile(pcm_file):
        print "(server_process) Found ", pcm_file
        # curva informativa canal L
        drc_l_mag_i[i] = pcm_fft (freq, int(fs), pcm_file)
        # Canal R:
        pcm_file = tmp + "-R.pcm"
        if os.path.isfile(pcm_file):
            print "(server_process) Found ", pcm_file
            # curva informativa canal R
            drc_r_mag_i[i] = pcm_fft (freq, int(fs), pcm_file)
            # Actualizamos el índice de DRCs disponibles:
            drc_index = i
        else:
            print "(server_process) ERROR en la secuencia de archivos DRC disponibles."
            print "(server_process) Se cancela la búsqueda de archivos DRC."
            break
    else:
        print "(server_process) Encontrados " + str(drc_index) + " archivos DRC."
        print "(server_process) Fin de la búsqueda de archivos DRC."
        break

### Curvas de PEQ (ecasound) informativas para la web:
peq_r_mag_i = np.zeros(len(freq))
peq_l_mag_i = np.zeros(len(freq))

last_level_change_timestamp = time.time()

# Recuperamos la configuración SysEQ del altavoz si se hubiera desactivado
do('syseq')

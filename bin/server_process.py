#!/usr/bin/env python
#coding=utf-8
# from __future__ import with_statement # This isn't required in Python 2.6
""" 
    Modulo core de FIRtro
"""
#----------------------------------------------------------------------
# Versión 2.0a (2016-oct)
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
#----------------------------------------------------------------------

import time
import ConfigParser
import socket
import sys
import json
import server_input
import soundcards
from numpy import *
from basepaths import *
from getconfig import *
from getstatus import *
from getspeaker import *
from getinputs import inputs
from subprocess import Popen
from math import copysign

## <PRESETS> (i) MAS ABAJO ESTAN DESTACADAS LAS LINEAS AFECTADAS
import presets
lista_de_presets = presets.lista_de_presets()

## <ECASOUND> para Ecualizador Paramétrico
# ecasound se ha cargado en modo server tcp/ip en el arranque (initfirtro.py)
import peq_control

## <MONO>
import monostereo

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
# Funcion para comunicarse con brutefir #
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

##############################################
# Funcion para obtener la fft de los pcm DRC #
##############################################
def pcm_fft (freq, fs, pcm_file, window_m=0):
    # Array que contendrá el fft simplificado para las frecuencias especificadas
    fft_mag = zeros(len(freq))
    # Abrimos el fichero en modo binario
    try:
        fd = open(pcm_file, 'rb')
        pcm = fromfile(file=fd, dtype=float32)
        fd.close()
    except: return fft_mag

    if (window_m<>0):
        # Enventanado
        w = blackman(window_m*2)
        # Nos quedamos con la parte derecha
        w = w[argmax(w):]
        pcm = pcm[0:len(w)]*w

    # Hacemos una fft y nos quedamos con la mitad, ya que la FFT es simétrica
    #fft = numpy.fft.fft(pcm)
    #m = fft.size
    #if (m % 2 == 0):
    #    fft = fft[0:m/2] #m par
    #else:
    #    fft = fft[0:((m-1)/2)+1] #m impar
    #m = fft.size
    
    # O hacemos directamente un rfft, que devuelve solamente las frecuencias positivas.
    # Ojo hay 1 muestra de diferencia.
    fft_data = fft.rfft(pcm)
    
    # Longitud de la fft
    m = fft_data.size
    
    # Convertimos a dB la parte absoluta
    fft_data = 20*log10(abs(fft_data))
    
    # Obtenemos las frecuencias en Hz. Tres metodos:
    fft_freq = linspace(0, fs/2, m) # Esto da solo freq positivas, para la longitud especificada
    # Esto da freq positivas y negativas correspondientes a una fft, hay que dividir el resultado:
    #fft_freq = fft.fftfreq(len(pcm),1./fs) 
    # Esto solo da las positivas, correspondietes a una rfft de la señal pcm:
    #fft_freq = fft.rfftfreq(len(pcm),1./fs)
    
    # Ahora buscamos los valores para las frecuencias especificadas
    for i in range(len(freq)):
        for j in range(len(fft_data)):
            if freq[i]-fft_freq[j]<0:
                fft_mag[i] = fft_data[j-1]
                break
    #return [round(float(data),2) for data in fft_mag_i.tolist()]
    return fft_mag

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
    write_speaker = False
    change_polarity = False
    do_mute = False
    gain_direct = False
    close = False
    quit = False
    exec_cmd = False
    exec_path = '/home/firtro/bin/'
    change_clock = False        ## v2.0a <CLOCK> recuperado de Testing3
    change_fs = False

    # Al poner este proceso en una función, las variables que estén definidas 
    # en los modulos importados hay que ponerlas como globales.
    # Si no se crean como locales, OjO
    global warnings
    global bass
    global treble
    global loudness_ref
    global loudness_track
    global loudness_level_info
    global input_gain
    global ref_level_gain
    global gain
    global level
    global maxlevel
    global headroom
    global balance
    global system_eq
    global preset               ## <PRESETS> ##
    global peq                  ## <PEQ> ##
    global drc_eq
    global polarity
    global filter_type
    global muted
    global input_name
    global resampled            ## posible entrada resampleada ##
    global mono                 ## <MONO> ##
    global replaygain_track
    global loudness_level_info
    global inputs
    global control_output
    global control_clear
    global tone_mag_i
    global loudeq_mag_i
    global syseq_mag_i
    global drc_r_mag_i
    global drc_l_mag_i
    global drc2_r_mag_i
    global drc2_l_mag_i
    global drc_index
    global fs                   ##
    global clock                ## <CLOCK> recuperado de Testing3 ##

    global brutefir_ports       ## v2.0 firtro_ports ##
    global ecasound_ports
    if load_ecasound:
        firtro_ports = ecasound_ports
    else:
        firtro_ports = brutefir_ports

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
    
    # Quitamos los caracteres finales
    order = order.rstrip('\r\n')
    # Separamos el comando de los argumentos
    line = order.split()
    if len(line) > 0: command = line[0]
    else: command = ""
    if len(line) > 1: arg1 = line[1]
    if len(line) > 2: arg2 = line[2]
    if len(line) > 3: arg3 = line[3]

    # Comprueba el comando y se decide las acciones a ejecutar:
    if control_output > 0:
        print "Command:", order
    try:
        if command == "status":
            write_status = False

        elif command == "input":
            if len(line) > 1:
                # name = arg1.lower()   # evitamos la restricción de hasta 3 argumentos
                name = " ".join(line[1:]).lower()
                print "NNNNNNNNNNNNNNNN", name
                if name == "restore":
                    # Si estoy restaurando la entrada, ya la tengo en input_name
                    change_input = True
                    change_gain = True
                    change_xovers = True
                    change_eq = True
                    muted = False
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
                if (int(arg1) < drc_index):
                    drc_eq = arg1
                    change_drc = True
            else: raise

        elif command == "preset":       ## <PRESETS> ##
            if len(line) > 1:
                #preset = arg1          # evitamos la restricción de hasta 3 argumentos
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
            write_speaker = True

        elif command == "syseq_off":
            system_eq = False
            change_eq = True
            write_speaker = True

        elif command == "exec":
            if len(line) > 1:
                exec_arg = arg1.translate(None,'/')
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

        # Si no se reconoce el comando
        else: raise
    except:
        warnings.append("Wrong command syntax")

    #                                                 #
    # Si no hubo excepciones, se pasa a la ejecución: #
    ###################################################

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

    # parametricos ECASOUND
    if change_peq:
        if load_ecasound:
            change_input = True # para reconectar la fuente a ecasound

            # hay tres casos para tener change_peq = True
            # 1) una actualizacion de preset (comando =  preset xxxx --> peq cambia)
            # 2) una recarga de un INI que se haya modificado (comando = peq_reload --> peq no cambia)
            # 3) un comando= peq_defeat --> peq cambia

            if "preset" in command or "reload" in command:
                if peq <> "off":
                    PEQini = loudspeaker_folder + loudspeaker + "/" + peq + ".peq"
                    peq_control.cargaPEQini(PEQini)
                else:
                    peq_control.PEQdefeat()
            elif "defeat" in command:
                peq_control.PEQdefeat()
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
            level += -6.0
        else:
            # esto simplemente desconecta las entradas.
            monostereo.setMono("off")
            # marcamos para restaurar las entradas
            change_input = True
            # y COMPENSAMOS NIVELES
            level += 6.0

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

    # Cambios de ganancia o EQ
    if (change_gain or change_eq):
        # Calculamos gain a partir del valor de level
        maxlevel = ceil(- input_gain - ref_level_gain)
        if not gain_direct:
            if level > maxlevel: level = maxlevel
            gain = level + input_gain + ref_level_gain
        else:
            # Si recibimos directamente el valor de gain, calculamos el level correspondiente 
            # (para comprobar que hay headroom suficiente)
            if gain > 0: gain = 0
            level =  gain - input_gain - ref_level_gain

        # Calculamos el headroom disponible
        level_headroom = -(level + input_gain + ref_level_gain)

        # Determinamos si se usa la fase en la EQ
        if filter_type == no_phase_xo: use_phase = False
        else: use_phase = True

        # Definimos la magnitud y fase de la EQ, inicializandolas a cero
        eq_mag = zeros(len(freq))
        eq_pha = zeros(len(freq))

        # Ponemos a cero la curva de tonos (informativa para la web)
        tone_mag_i = zeros(len(freq))

        # Ponemos a cero la curva de EQ sistema (informativa para la web)
        syseq_mag_i = zeros(len(freq))

        # Calculamos el loudness en caso de que estÈ activo
        if loudness_track:
            change_eq = True
            if abs(loudness_ref) > loudness_variation: loudness_ref = copysign(loudness_variation, loudness_ref)
            loudness_i = loudness_SPLmax - (level + loudness_SPLref + loudness_ref)
            loudness_max_i = loudness_SPLmax - loudness_SPLmin
            if loudness_i < 0: loudness_i = 0
            if loudness_i > loudness_max_i: loudness_i = loudness_max_i
            loudeq_mag = loudness_mag_curves[:,loudness_i]
            eq_mag += loudeq_mag
            loudness_level_info = str(int(loudness_i - loudness_SPLmax + loudness_SPLref)) \
                                      + ' (' + str(round(max(loudeq_mag),2)) + ' dB)'
            if use_phase:
                eq_pha += loudness_pha_curves[:,loudness_i]
            loudeq_mag_i = [round(float(data),2) for data in loudness_mag_curves[:,loudness_i].tolist()] # Info para la web
            #print loudeq_mag
        else: loudeq_mag_i = [ 0 for i in freq]

        # Calulamos la EQ de sistema
        if system_eq:
            eq_mag += syseq_mag
            syseq_mag_i += syseq_mag # Info para la web
            if use_phase:
                eq_pha += syseq_pha

        # Calculamos la EQ de agudos
        if treble != 0:
            treble_i = tone_variation - treble
            if treble_i < 0: treble_i = 0
            if treble_i > 2 * tone_variation: treble_i = 2 * tone_variation
            eq_mag += treble_mag[:,treble_i]
            if use_phase:
                eq_pha += treble_pha[:,treble_i]
            treble = tone_variation - treble_i
            tone_mag_i+= treble_mag[:,treble_i] # Info para la web

        # Calculamos la EQ de graves
        if bass != 0:
            bass_i = tone_variation - bass
            if bass_i < 0: bass_i = 0
            if bass_i > 2 * tone_variation: bass_i = 2 * tone_variation
            eq_mag += bass_mag[:,bass_i]
            if use_phase:
                eq_pha += bass_pha[:,bass_i]
            bass = tone_variation - bass_i
            tone_mag_i+= bass_mag[:,bass_i] # Info para la web

        # Ahora el tipo de datos de la variable "tone_mag_i" es numpy.ndarray, demasiado complejo para enviarlo via JSON
        # Lo convertimos a lista tipo float, redondeado

        if isinstance(tone_mag_i, ndarray): tone_mag_i = [round(float(data),2) for data in tone_mag_i.tolist()]
        #tone_mag_i = [round(float(data),2) for data in tone_mag_i.tolist()]

        # En este punto tenemos la EQ total a aplicar
        # Determinamos el máximo nivel de amplificación
        eq_level = max(eq_mag)
        headroom = round(level_headroom - eq_level,2)
        if headroom == -0: headroom = 0
        # Aplicamos los cambios de level y/o EQ si hay headroom suficiente
        if eq_level <= level_headroom:
            if change_gain:
                gain_0 = gain
                gain_1 = gain
                if abs(balance) > balance_variation: balance = copysign(balance_variation,balance)
                if balance > 0: gain_0 = gain_0 - balance
                elif balance < 0: gain_1 = gain_1 + balance
                bf_cli('cfia 0 0 ' + str(-gain_0) + ' ; cfia 1 1 ' + str(-gain_1))
                # 2º Entrada de brutefir (para analogica con filtros mp):
                # bf_cli('cfia 2 2 ' + str(-gain_0) + ' ; cfia 3 3 ' + str(-gain_1)) 
                muted = False
            if change_eq:
                eq_str = ""
                l = len(freq)
                for i in range(l):
                    eq_str = eq_str + str(freq[i]) + '/' + str(eq_mag[i])
                    if i != l: eq_str += ", "
                bf_cli('lmc eq 0 mag ' + eq_str)
                eq_str = ""
                for i in range(l):
                    eq_str = eq_str + str(freq[i]) + '/' + str(eq_pha[i])
                    if i != l: eq_str += ", "
                bf_cli('lmc eq 0 phase ' + eq_str)
        else:
            #Si no hay headroom, no aplicamos los cambios, y recuperams los valores anteriores
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

    # Resto de comandos
    if do_mute:
        bf_cli("cfia 0 0 m0 ; cfia 1 1 m0")
        #bf_cli("cfia 2 2 m0 ; cfia 3 3 m0") # 2º Entrada de brutefir (para analogica con filtros mp)

    if change_polarity:
        bf_cli('cfia 0 0 m' + polarity + '1 ; cfia 1 1 m' + polarity + '1')
        #bf_cli('cfia 2 2 m' + polarity + '1 ; cfia 3 3 m' + polarity + '1') # 2º Entrada de brutefir (para analogica con filtros mp)

    # (!) sustituido se ha pasado al inicio con la gestión de <PRESETS>
    #if change_xovers:
    #    for channel in speaker.options("out_channels"):
    #        bf_filter='"f_' + speaker.get("out_channels", channel).split()[0] + '"'
    #        bf_coeff='"c_' + filter_type + '-' + speaker.get("out_channels", channel).split()[1] + '"'
    #        bf_cli('cfc ' + bf_filter + ' ' + bf_coeff)

    if change_drc:
        # Metodo 1: Se asignan siempre coeficientes predefinidos. drc0 est· definido con un dirac pulse, y no tiene efecto
        #bf_cli('cfc "f_drc_L" "c_drc' + drc_eq + '_L"; cfc "f_drc_R" "c_drc' + drc_eq + '_R"')

        # Metodo 2: Si el drc es 0, entonces se asigna el coeficiente -1, optimizando latencia y uso de procesador
        if drc_eq == "0":
            bf_cli('cfc "f_drc_L" -1; cfc "f_drc_R" -1')
            #bf_cli('cfc "f_drc_L2" -1; cfc "f_drc_R2" -1') # 2º Entrada de brutefir (para analogica con filtros mp)
        else:
            bf_cli('cfc "f_drc_L" "c_drc' + drc_eq + '_L"; cfc "f_drc_R" "c_drc' + drc_eq + '_R"')
            #bf_cli('cfc "f_drc_L2" "c_drc' + drc_eq + '_L"; cfc "f_drc_R2" "c_drc' + drc_eq + '_R"') # 2º Entrada de brutefir (para analogica con filtros mp)

    # EQ global aplicada (drc + syseq), Info para la web
    if (change_gain or change_eq or change_drc):
        if int(drc_eq) < len(drc_r_mag_i):
            drc2_r_mag_i = [round(float(data),2) for data in (drc_r_mag_i[int(drc_eq)] + syseq_mag_i).tolist()]
        else:
            drc2_r_mag_i = [round(float(data),2) for data in (syseq_mag_i).tolist()]

        if int(drc_eq) < len(drc_l_mag_i):
            drc2_l_mag_i = [round(float(data),2) for data in (drc_l_mag_i[int(drc_eq)] + syseq_mag_i).tolist()]
        else:
            drc2_l_mag_i = [round(float(data),2) for data in (syseq_mag_i).tolist()]

    if exec_cmd:
        result = Popen(exec_path + exec_arg, shell=True)

    if write_status:
        status.set('loudness EQ', 'loudness_track', loudness_track)
        status.set('loudness EQ', 'loudness_ref', loudness_ref)
        status.set('recording EQ', 'bass', bass)
        status.set('recording EQ', 'treble', treble)
        status.set('level', 'level', level)
        status.set('level', 'headroom', headroom)
        status.set('level', 'balance', balance)
        status.set('general', 'drc_eq', drc_eq)
        status.set('general', 'polarity', polarity)
        status.set('general', 'filter_type', filter_type)
        status.set('general', 'muted', muted)
        status.set('inputs', 'input', input_name)
        status.set('general', 'clock', clock)           ## <CLOCK> recuperado de Testing3
        status.set('general', 'fs', fs)
        status.set('inputs', 'resampled', resampled)    ## input por tarjeta resampleada
        status.set('inputs', 'mono', mono)              ## <MONO> ##
        status.set('general', 'preset', preset)         ## <PRESETS> ##
        status.set('general', 'peq', peq)               ## <PEQ> ##
        try:
            statusfile = open(status_path, 'w')
            status.write(statusfile)
            statusfile.close()
        except:
            warnings.append("Failed to open status file" + status_path)

    if write_speaker:
        speaker.set('equalization', 'system_eq', system_eq)
        try:
            speakerfile = open(speaker_path, 'w')
            speaker.write(speakerfile)
            speakerfile.close()
        except:
            warnings.append("Failed to open speaker file" + status_path)

    # Mostramos en pantalla un resumen del estado
    if control_output>0:
        print '----'
        print 'Filter Type =', filter_type
        print 'Gain =', gain
        if not muted: 
            print 'Level =', str(level)
        else: 
            print 'Level =', str(level) + " (MUTED)"
    if control_output>1:
        print 'Ref level gain =', ref_level_gain
        print 'Input gain =', input_gain
        print 'Headrooom =', str(headroom) + ' dB'
        print 'Balance =', balance
        print '---'
        print 'Preset =', preset                        ## <PRESET> ##
        print '----'
        print 'PEQ =', peq
        print 'DRC =', drc_eq
        if loudness_track:
            print 'Loudness =', loudness_level_info
            print 'Loudness ref =', loudness_ref
        else:
            print 'Loudness (off)'
        if system_eq:
            print 'System EQ =', 'Yes (' + str(round(max(syseq_mag),2)) + ' dB)'
        else:
            print 'System EQ (off)'
        print 'Treble =', treble
        print 'Bass =' , bass
        print 'Mono =' , mono                           ## <MONO> ##
        print '---'
        print 'Input =', input_name
        print 'Fs =', fs + ' Hz [clock = ' + str(clock) + ']' ## v2.0a recuperado <CLOCK> Testing3
        print '---'

    # Imprimimos los warnings que se hayan producido
    if len(warnings)>0:
        print "(server_process) Warnings:"
        for warning in warnings:
            print "\t" + warning

    # Obtenemos el diccionario con todas la variables y sus valores
    # Variables globales
    data = locals()
    # Añadimos las variables locales
    data.update(globals())
    # Y la lista de entradas
    data.update({'inputs':inputs.sections()})
    # En esta lista almacenamremos las variables que queremos extraer del dicionario global
    keys = ['treble', 'bass', 'replaygain_track', 'level', 'maxlevel', 'headroom', 'muted', 'polarity',
        'fs', 'drc_eq', 'filter_type', 'clock', 'loudness_track', 'loudness_ref', 'loudness_level_info',
        'radio', 'input_name', 'input_gain', 'system_eq', 'room_gain', 'house_corner', 'house_atten',
        'ref_level_gain', 'loudspeaker', 'inputs', 'warnings', 'order','freq_i','tone_mag_i','loudeq_mag_i',
        'drc2_r_mag_i','drc2_l_mag_i','drc_index','balance','balance_variation',
        'preset', 'lista_de_presets', 'mono', 'peq'] ## <PRESETS> y <MONO> ##
    # Y obtenemos un nuevo diccionario filtrado, con solo las opciones que nos interesan
    fdata = { key: data[key] for key in keys}
    # Lo formateamos y lo mandamos como salida de la función
    fdata = json.dumps (fdata)
    # Devolvemos el diccionario
    return (fdata)

###############################
# Inicializacion de variables #
###############################
try:
    freq = loadtxt(freq_path)
    loudness_mag_curves = loadtxt(loudness_mag_path)
    loudness_pha_curves = loadtxt(loudness_pha_path)
    syseq_mag = loadtxt(syseq_mag_path)
    syseq_pha = loadtxt(syseq_pha_path)
    treble_mag = loadtxt(treble_mag_path)
    treble_pha = loadtxt(treble_pha_path)
    bass_mag = loadtxt(bass_mag_path)
    bass_pha = loadtxt(bass_pha_path)
except:
    print "(server_process) Error: Failed to load EQ files"
    sys.exit(-1)

input_gain = 0
eq_level = 0
gain = level + input_gain + ref_level_gain
maxlevel = 0
loudness_level_info = ""
warnings = []

# Informacion de las frecuencias utilizadas para la EQ
freq_i = [ int(i) for i in freq]

# Informacion de las curvas calculadas. Las inicializo a cero
syseq_mag_i = zeros(len(freq))
drc_r_mag_i ={}
drc_l_mag_i ={}
drc2_r_mag_i = [ 0 for i in freq] #drc+syseq
drc2_l_mag_i = [ 0 for i in freq] #drc+syseq
tone_mag_i = [ 0 for i in freq]
loudeq_mag_i = [ 0 for i in freq]

# Calculamos las curvas de los coeficientes DRC
drc_index=0
drc_r_mag_i[drc_index]=zeros(len(freq))
drc_l_mag_i[drc_index]=zeros(len(freq))

# Buscamos todos los ficheros pcm que existan
print "(server_process) Doing FFT of DRC pcm files..."
while True:
    drc_index=drc_index+1
    pcm_file = loudspeaker_folder + loudspeaker + '/' +fs + "/drc-" + str(drc_index) + "-R.pcm"
    if os.path.isfile(pcm_file):
        print "(server_process) Found", pcm_file
        drc_r_mag_i[drc_index] = pcm_fft (freq,int(fs),pcm_file)
    else: break
    pcm_file = loudspeaker_folder + loudspeaker + '/' +fs + "/drc-" + str(drc_index) + "-L.pcm"
    if os.path.isfile(pcm_file):
        print "(server_process) Found", pcm_file
        drc_l_mag_i[drc_index] = pcm_fft (freq,int(fs),pcm_file)
    else: break
# drc_index nos sirve ahora para saber el máximo drc que se puede aplicar. [0...drc_index-1]

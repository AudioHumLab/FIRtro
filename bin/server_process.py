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
# - Se incluye 'system_eq' en el archivo de estado "audio/status"
#   y se deja modificar el archivo "lspk/altavoz/speaker" ahora solo de lectura.
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
# v2.0f
# - mpd client slider LOG_volume
#
# v2.0g
# - Se desliga el cambio de xover lp|mp de los presets.
# - Se hace un mute antes de que un nuevo preset conecte nuevas vías para evitar escucharlas
#   sin la necesaria EQ de sal que se aplicará a continuación.
# - Se corrige change_inputs: se recarga el xover de audio/inputs solo si change_xovers=True
# - Mejoras en los comentarios del código.. y reubicación de algunas de las recientes novedades..
#
#----------------------------------------------------------------------

import time
import ConfigParser
import socket
import sys
import json
from subprocess import Popen
from math import copysign
import numpy as np
from scipy import signal

import server_input

from basepaths import *
from getconfig import *
from getstatus import *
from getspeaker import *
from getinputs import inputs

##################################################################
# (i) FIRtro 2.0 EN ADELANTE SE DESTACARÁN LAS LINEAS AFECTADAS  #
##################################################################
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

import read_brutefir_process as brutefir ## v2.0g
import brutefir_cli


################################################################
################################################################
####            Funciones AUXILIARES:                       ####
################################################################
################################################################

################################################################
### AUX. Comprueba que exista el directorio de una Fs requerida
################################################################
def check_fs_directory(fs):
    fsPath = loudspeaker_folder + loudspeaker + "/" + format(fs)
    if os.path.exists(fsPath):
        return True
    else:
        print "(server_process) Directory not found: " + fsPath
        return False

################################################################
### AUX. Funcion para enviar comandos a Brutefir
################################################################
def bf_cli (orden):
    global warnings
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((bfcli_address, bfcli_port))
        s.send(orden + '; quit\n')
        s.close()
    except socket.error, (value, msg):
        s.close()
        error = "Brutefir: " +"[Errno " + str(value) +"] " + msg
        if error not in warnings: 
            warnings.append (error)

################################################################
### AUX. Funcion para obtener la fft de los pcm DRC
#   Nota: mismos bins que los del array 'freq' del EQ de Brutefir.
################################################################
def pcm_fft (freq, fs, pcm_file, window_m=0):
    # Array que contendrá el fft simplificado para las frecuencias especificadas
    fft_mag = [0] * len(freq)
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

################################################################
### AUX. Funcion para obtener la FR de un EQ paramétrico
#   Nota: mismos bins que los del array 'freq' del EQ de Brutefir.
################################################################
def peq2mag_i (peqFile, channel):
    Fs = int(fs)
    mag_i = [0] * len(freq)

    # Filtros paramétricos (frec, BWoct, gain):
    peqs = peq2fr.leePEQ_canal(peqFile, channel)
    # Array con la respuesta en frecuencia [(w, h), ...] de cada filtro paramétrico:
    FRs  = peq2fr.peqBW_2_fr(Fs, peqs)
    # respuesta combinada de todos los paramétricos (w, h):
    w, h = peq2fr.frSum(Fs, FRs)
    # en dBs:
    hdB = 20 * np.log10(np.abs(h))

    f = w * Fs/(2*np.pi)    # w normalizadas --> frecuencias reales.

    # Ahora queda trasladar la respuesta (calculada con Fs) a los 63
    # valores de frecuencia 'freq' de la etapa EQ y manejados en las gráficas de la web.
    
    # Y usamos el algoritmo de Alberto (ver función pcm_ftt) para completar los 63 valores:
    for i in range(len(freq)):
        for j in range(len(hdB)):
            if freq[i]-f[j] < 0:
                mag_i[i] = hdB[j-1]
                break

    return mag_i

################################################################
### AUX. V2.0c El diccionario de estado devuelto por do(order)
################################################################
def firtroData(locales, globales, entradas):
    # Obtenemos el diccionario con todas la variables y sus valores
    # 1. Variables locales
    data = locales
    # 2. añadimos las variables globales
    data.update(globales)
    # 3. y la lista de entradas
    data.update({'inputs':entradas})
    
    # Variables que nos interesan del dicionario general 'data':
    keys = ['treble', 'bass', 'replaygain_track', 'level', 'maxlevel_i', 'headroom', 'muted', 'polarity',
        'fs', 'drc_eq', 'filter_type', 'clock', 'loudness_track', 'loudness_ref', 'loudness_level_info',
        'radio', 'input_name', 'input_gain', 'system_eq', 'room_gain', 'house_corner', 'house_atten',
        'ref_level_gain', 'loudspeaker', 'inputs', 'warnings', 'order','freq_i','tone_mag_i','loudeq_mag_i',
        'drcTot_r_mag_i','drcTot_l_mag_i','drc_index','balance','balance_variation',
        'preset', 'lista_de_presets', 'mono', 'peq', 'peqdefeat']    ## <PRESETS> <MONO> <PEQ> ##
    # Y obtenemos un nuevo diccionario filtrado, con solo las opciones que nos interesan
    fdata = { key: data[key] for key in keys}
    # Lo formateamos y lo mandamos como salida de esta función:
    fdata = json.dumps(fdata)
    # Devolvemos el diccionario
    return fdata

###############################################################
###############################################################
####    FUNCION PRINCIPAL do(order) para procesa ordenes   ####
###############################################################
###############################################################
def do (order):

    ####  (i) Acceso a VARIABLES GLOBALES (incluyendo las importadas):
    
    global warnings             # Avisos runtime

    global ref_level_gain       # Ganancia del altavoz ref al SPL nominal (/lspk/altavoz/speaker)
    global gmax                 # Tope de ganacia admitido en Brutefir (audio/config)

    global fs
    global clock                ## <CLOCK> recuperado de Testing3 ##

    global gain, level, headroom, balance, muted, polarity, filter_type, replaygain_track
    global bass, treble, loudness_ref, loudness_track, loudness_level_info
    global mono, monoCompens    ## <MONO> ##

    global system_eq, drc_eq
    global preset               ## <PRESETS> ##
    global peq, peqdefeat       ## <PEQ> ##

    global inputs
    global input_name, input_gain, resampled
    global radio, radio_prev    # v2.0e se centraliza la gestión de la radio tdt aquí

                                # Curvas informativas para la web
    global tone_mag_i, loudeq_mag_i, syseq_mag_i, drc_l_mag_i, drc_r_mag_i
    global drcTot_l_mag_i
    global drcTot_r_mag_i       # Las curvas 'drcTot' incluyen DRC_fir + sysEQ + PEQ
    global drc_index
    global peq_l_mag_i          ## <PEQ> ##
    global peq_r_mag_i

    global brutefir_ports       ## v2.0 'firtro_ports' ##
    global ecasound_ports

    global last_level_change_timestamp      ## Usado solo por <MPD> ##

    global control_output       # Gestión de printados por consola
    global control_clear        # Sin uso

    #### Inicialización de las acciones a tomar en este procesamiento do(order)
    
    write_status = True         # Normalmente se refrescará el archivo de estado audio/status
    warnings = []               # Borramos los warnings
    change_gain = False
    change_eq = False
    change_xovers = False
    change_drc = False
    change_preset = False       ## <PRESETS> ##
    change_peq = False
    change_input = False
    change_mono = False         ## <MONO> ##
    change_polarity = False
    do_mute = False
    gain_direct = False
    exec_cmd = False
    exec_path = '/home/firtro/bin/'
    change_clock = False        ## v2.0a <CLOCK> recuperado de Testing3
    change_fs = False
    change_radio = False

    #### Memorizamos ajustes para poder restaurarlos si no se pudieran aplicar (e.g. por falta de headroom)
    
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
    preset_old              = preset        ## <PRESETS> ##
    drc_eq_old              = drc_eq
    peq_old                 = peq           ## <PEQ> ##
    fs_old                  = fs            ## <CLOCK> ##
    clock_old               = clock
    input_name_old = input_name
    filter_type_old = filter_type
    mono_old = mono                         ## <MONO> ##
    radio_old = radio
    radio_prev_old = radio_prev
    
    #############################################################
    ##        Leemos la orden solicitada 'do(order)'           ##
    ##        y se deciden las acciones correspondientes       ##
    #############################################################

    #########################################################
    #     <MPD> control de volumen de MPD ligado a FIRtro
    # (i) INTERRUMPIMOS EL PROCESAMIENTO si se tratase de una
    # orden gain rebotada por mpd inmediatamente después 
    # de haber ajustado aquí el volumen del sistema.
    #########################################################
    if mpd_volume_linked2firtro:
        if (time.time() - last_level_change_timestamp) < MPD_GAIN_FWD_TIMER:
            #print "(server_process) comando descartado: " + order + \
            #      " (reason MPD_GAIN_FWD_TIMER=" + str(MPD_GAIN_FWD_TIMER) + ")" # DEBUG
            dicci_estado = firtroData(locals(), globals(), inputs.sections())
            return dicci_estado

    order = order.rstrip('\r\n')            # Quitamos los caracteres finales
    line = order.split()                    # Separamos el comando de los argumentos
    if len(line) > 0:   command = line[0]
    else:               command = ""
    if len(line) > 1: arg1 = line[1]
    if len(line) > 2: arg2 = line[2]
    if len(line) > 3: arg3 = line[3]
    
    if control_output > 0:                  # Printa por consola
        print "(server_process) Command:", order

    ### Acciones a tomar según el comando o RAISE
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
                change_gain = True
            else: raise

        elif command == "level_add":
            if len(line) > 1:
                level += float(arg1)
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
                change_xovers = True
            else: raise

        elif command == "drc":
            if len(line) > 1:
                if (int(arg1) <= drc_index):
                    drc_eq = arg1
                    change_drc = True
            else:
                raise

        elif command == "preset":           ## <PRESETS> ##
            if len(line) > 1:
                preset = " ".join(line[1:]) # evitamos la restricción arg1 ... arg3
                change_preset   = True
                change_drc      = True      ## pq los preset tienen un DRC asociado
                change_gain     = True      ## pq tb tienen ajuste de balance
                change_peq      = True      ## pq tb tienen ajuste de PEQ
            else: raise

        elif command == "peq_reload":       ## <PEQ> ##
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

        elif command == "syseq_off":
            system_eq = False
            change_eq = True

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

        # (!) RAISE SI NO SE RECONOCE EL COMANDO
        else:
            raise

    except:
        warnings.append("Wrong command syntax")

    ###################################################
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
    if change_preset:
                
        # (i)   Muteamos temporalmente Brutefir para evitar oir las nuevas vias sin la la nueva EQ de sala,
        #       por ejemplo en el caso de un nuevo subwooer muy dependiente de compensación del
        #       room gain escucharemos un grave muy inflado hasta que no se aplica la EQ.
        #       El desmuteo no es necesario, ya que change_preset implica change_gain.
        bf_cli("cfia 0 0 m0 ; cfia 1 1 m0")
        #       Este sleep es experimental 350 ms sirve para que lo dicho arriba se cumpla.
        #       La cosa es que el muteo tarda demasiado en ejecutarse :-/
        time.sleep(.350)
        
        # (i) OjO: los preset incluyen un DRC y BALANCE asociados, entonces
        # a la vez que configuramos las vias para el preset, obtenemos el drc y el balance que le corresponde:
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
    #   (*)Nota: en cada do() traducimos los paramétricos a curvas de respuesta informativas para
    #            la web para permitir cambios al vuelo del archivo 'lspk/altavoz/xxx.peq'.
    if change_peq:
        if load_ecasound:

            ## MUTEAMOS temporalmente Brutefir para evitar oir la interrupción durante la carga de los paramétricos.
            #  Antes tomamos nota de la atten de la señal para poder desmutear bien.
            tmp = brutefir_cli.bfcli("lf;quit;") # lee brutefir pero no pone el ';quit' como en 'bf_cli' de este módulo.
            bfAtten0 = [x for x in tmp.split("\n") if ("from inputs:  0" in x)][-1].split("/")[-1]
            bfAtten1 = [x for x in tmp.split("\n") if ("from inputs:  1" in x)][-1].split("/")[-1]
            bf_cli("cfia 0 0 m0 ; cfia 1 1 m0")

            peqdefeat = False
            change_input = True     # para reconectar la fuente a ecasound
            # curvas informativas para la web (*):
            peq_l_mag_i = [0] * len(freq)
            peq_r_mag_i = [0] * len(freq)
            if "preset" in command or "reload" in command:
                if peq <> "off":
                    PEQini = loudspeaker_folder + loudspeaker + "/" + peq + ".peq"
                    peq_control.cargaPEQini(PEQini)
                    # curvas informativas para la web (*):
                    peq_l_mag_i = peq2mag_i(PEQini, "left")
                    peq_r_mag_i = peq2mag_i(PEQini, "right")
                else:
                    peq_control.PEQdefeat()
                    peqdefeat = True
            elif "defeat" in command:
                peq_control.PEQdefeat()
                peqdefeat = True

            # y DESMUTEAMOS:
            bf_cli("cfia 0 0 " + bfAtten0 +" m0; cfia 1 1 " + bfAtten1 + "m0")

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

    ## v2.0a <CLOCK> se había perdido, se ha recuperado de Testing3 (OjO se ha reescrito).
    ## nota: Los cambios de CLOCK o de FS pueden ser:
    ##          -> explícitos en un comando "clock"
    ##          -> implícitos en un comando "input"
    if change_input:

        if load_ecasound:   firtro_ports = ecasound_ports
        else:               firtro_ports = brutefir_ports

        input_gain  = float(inputs.get(input_name, "gain"))
        input_ports =       inputs.get(input_name, "in_ports")

        if change_xovers: # v2.0g
            filter_type =   inputs.get(input_name, "xo")

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
            # SI NO HAY CAMBIO DE Fs o de CLOCK
            if not change_clock and not change_fs:
                # SE CAMBIA la INPUT:
                if not server_input.change_input (input_name, \
                                                  input_ports.split(), \
                                                  firtro_ports.split(), \
                                                  resampled):
                    # Si falla el cambio de input:
                    warnings.append("Error changing to input " + input_name)
                    input_name      = input_name_old
                    filter_type     = filter_type_old
                    change_xovers   = False
                    change_eq       = False
                    change_gain     = False
                    write_status    = True
            else:
                # DEJAMOS que change_clock/change_fs REINICIE el AUDIO del FIRtro
                pass
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

    # (!) revisar esto : ¿gain o level?  ¡¡¡OjO!!! PENDIENTE long time ago
    #if replaygain_track:
    #    gain += loudness_ref

    ###################################################
    #          MÁQUINA DE CONTROL DE VOLUMEN
    #  Gestiona los cambios de ganancia o de EQ, con
    #  control de clipping debido a input_gain y eq_mag.
    ###################################################
    if (change_gain or change_eq):

        # Info para un potenciómetro de volumen externo (p.ej el slider de la web) (recálculo)
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
                # (!) Para evitar que arranque sin atenuacion si partimos de muted=True:
                else:
                    bf_cli('cfia 0 0 m0; cfia 1 1 m0')
                    # AMR 2º Entrada de brutefir (para analogica con filtros mp):
                    #bf_cli('cfia 2 2 m0; cfia 3 3 m0')
                if not gain_direct and "level" in order and mpd_volume_linked2firtro:        ## <MPD> ##
                    # update MPD "fake volume"
                    vol = 100*(np.exp(max((gain/client_mpd.slider_range+1),0)**(1/1.293)*np.log(2))-1)
                    if vol < 1: vol = 1 # minimal mpd volume
                    client_mpd.setvol(vol)
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

    ############################################
    ####        Resto de acciones:          ####
    ############################################
    
    if do_mute:
        bf_cli("cfia 0 0 m0 ; cfia 1 1 m0")
        # 2º Entrada de brutefir (para analogica con filtros mp)
        #bf_cli("cfia 2 2 m0 ; cfia 3 3 m0")

    if change_polarity:
        bf_cli('cfia 0 0 m' + polarity + '1 ; cfia 1 1 m' + polarity + '1')
        # 2º Entrada de brutefir (para analogica con filtros mp)
        #bf_cli('cfia 2 2 m' + polarity + '1 ; cfia 3 3 m' + polarity + '1')

    if change_xovers: ## v2.0f ##
        # Leemos en tiempo real los coeff cargados en los filtros de vías de Brutefir
        # NOTA: en FIRtro 1.0 se leia speaker.get("out_channels", channel) que queda en desuso
        #       por ser un mapeo que solo servía para resolver esta función.

        # Añadimos la posibilidad de ALTERNAR el filter_type para usarse desde un botón de la web:
        if filter_type in ["cambia", "alterna", "change", "switch", "toggle"]:
            if filter_type_old == "lp": filter_type = "mp"
            else:                       filter_type = "lp"
        elif not filter_type in ["lp", "mp"]:
            filter_type = filter_type_old

        # Solo procede hacer change_xovers lp|mp en los filtros de vías:
        etiquetasDeVias = ["fr", "lo", "mi", "hi", "sw"]
        haLeidoBfir = True
        try:
            brutefir.lee_config()
        except:
            haLeidoBfir = False
            print "(server_process) ERROR usando read_brutefir_process.py"
        try:
            brutefir.lee_running_config()
        except:
            haLeidoBfir = False
            print "(server_process) ERROR usando read_brutefir_process.py"
        if haLeidoBfir:
            for filter_running in brutefir.filters_running:
                # ejemplo: ['f_lo_L', '12', 'c_lp-lo4', 'lp-lo.pcm']
                bfilter, coeffNum, coeffName, pcmName = filter_running
                if [x for x in etiquetasDeVias if x in bfilter]:        # aquí verificamos que sea una etapa de filtro de vias
                    newCoeffName = "c_" + filter_type + "-" + coeffName[5:]
                    tmp = 'cfc "' + bfilter + '" "' + newCoeffName + '"; quit;'
                    bf_cli(tmp)

    if change_drc:
        # Si el drc es 0, entonces se asigna el coeficiente -1 optimizando latencia y uso de procesador:
        if drc_eq == "0":
            bf_cli('cfc "f_drc_L" -1; cfc "f_drc_R" -1')
            # (amr) 2º Entrada de brutefir (para analogica con filtros mp)
            #bf_cli('cfc "f_drc_L2" -1; cfc "f_drc_R2" -1')
        else:
            bf_cli('cfc "f_drc_L" "c_drc' + drc_eq + '_L"; cfc "f_drc_R" "c_drc' + drc_eq + '_R"')
            # (amr) 2º Entrada de brutefir (para analogica con filtros mp)
            #bf_cli('cfc "f_drc_L2" "c_drc' + drc_eq + '_L"; cfc "f_drc_R2" "c_drc' + drc_eq + '_R"')

    # Curvas info para la web - EQ global aplicada (drc + syseq):
    if (change_gain or change_eq or change_drc or change_peq):
        # L:
        if int(drc_eq) < len(drc_l_mag_i):
            drcTot_l_mag_i = [round(float(data),2) for data in (drc_l_mag_i[int(drc_eq)] + syseq_mag_i + peq_l_mag_i).tolist()]
        else:
            drcTot_l_mag_i = [round(float(data),2) for data in (syseq_mag_i + peq_l_mag_i).tolist()]
        # R:
        if int(drc_eq) < len(drc_r_mag_i):
            drcTot_r_mag_i = [round(float(data),2) for data in (drc_r_mag_i[int(drc_eq)] + syseq_mag_i + peq_r_mag_i).tolist()]
        else:
            drcTot_r_mag_i = [round(float(data),2) for data in (syseq_mag_i + peq_l_mag_i).tolist()]

    if exec_cmd:
        result = Popen(exec_path + exec_arg, shell=True)

    if system_eq:                                   # para no mostrar los valores
        rg_tmp = room_gain; ha_tmp = house_atten    # cuando están desactivados
    else:
        rg_tmp = ha_tmp = "0"

    ################################################
    # ACTUALIZA EL ARCHIVO DE ESTADO (audio/status)
    ################################################
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
    dicci_estado = firtroData(locals(), globals(), inputs.sections())
    return dicci_estado



################################################################################
##########################    INICIALIZACIONES:    #############################
################################################################################

### NIVEL:
input_gain = 0
gain = level + input_gain + ref_level_gain
# <MONO> no computa en el cálculo de headroom, se sumará a la ganancia final enviada a Brutefir.
if mono == "on":
    monoCompens = -6.0
else:
    monoCompens = -0.0
# <MPD> control de volumen de MPD ligado a FIRtro
last_level_change_timestamp = time.time()

# <PRESETS>
lista_de_presets = presets.lista_de_presets()

# <PEQ>
peqdefeat = False

### Leemos las CURVAS EQ que se renderizadarán en 'eq' de Brutefir
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

####################################################
### VARIABLES INFORMATIVAS para sistemas de control:
####################################################
warnings = []
# String informativa del loudness aplicado
loudness_level_info = ""

### Información de estado útil para un potenciómetro de volumen externo (p.ej el slider de la web)
maxlevel_i = gmax - ref_level_gain - input_gain

### Informacion de las frecuencias utilizadas para la etapa de EQ
freq_i = [ int(i) for i in freq] # No podemos hacer freq_i = freq porque resultaría en un alias

### Inicialización de curvas informativas (xxx_i) para las gráficas DRC de la página web.
syseq_mag_i     = [0] * len(freq)
drc_l_mag_i     = {}                    # diccionarios de curvas
drc_r_mag_i     = {}
peq_r_mag_i     = [0] * len(freq)       ## <PEQ ##
peq_l_mag_i     = [0] * len(freq)
drcTot_l_mag_i  = [0] * len(freq)       # drcTot : drc + peq + syseq
drcTot_r_mag_i  = [0] * len(freq)
tone_mag_i      = [0] * len(freq)
loudeq_mag_i    = [0] * len(freq)

### Carga de las curvas informativas para la web de los pcm disponibles para DRC:
# (i) El diseño original en FIRtro v1.0 requiere los nombres
#     de archivos pcm para drc numerados correlativamente desde 1.
#     El mecanismo de selección de DRC reserva el índice 0 para "drc plano".
drc_index = 0
drc_r_mag_i[drc_index] = [0] * len(freq)
drc_l_mag_i[drc_index] = [0] * len(freq)
# Buscamos todos los ficheros pcm de drc que existan: 
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

### Carga de las curvas informativas para la web de PEQ:
#   NOTA:   Las releemos en cada do('peq_reload') para permitir
#           cambios al vuelo de los paramétricos del archivo 'lspk/altavoz/xxx.peq'

# Recuperamos la configuración SysEQ del altavoz si se hubiera desactivado
do('syseq')

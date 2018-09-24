#!/usr/bin/env python
# -*- coding: utf-8 -*-

###################################################################################################
#################################   DISCLAIMER ACHTUNG   ##########################################
#                ESTE SCRIPT ES MUY RUDIMENTARIO QUEDA PENDIENTE
#                REESCRIBIRLO INCLUYENDO EL SCANEO DE PCMs Y TAL :-/
###################################################################################################

# v1.0: se permite argumento "-w" para escribir la salida en el archivo brutefir_config
# v1.1: incorpora un coeff de xover "dirac pulse" para poder cargarlo en una vía full range alineada con otras.
# v1.2: se permiten nuevos argumentos:
#     - un archivo brutefir.ini alternativo
#     - una carpeta de altavoz distinta de la configurada en el sistema en audio/config
# v1.2a:
#   - Los coeff de cruce se dejan de agrupar primero lp y luego mp,
#     se printan por parejas lp/mp para mejor visibilidad de las atenuaciones de cada coeff.
# v1.2b:
#   - Se adaptan las etapas de filtrado eq y drc para podeer hacer MONO: drc recibe ambos canales de eq.
# v1.2c:
#   - Bug se leia <audio_folder>/filters.ini antes del escaneo (ahora llamado filters.scan)
#   - Ahora se debe indicar la carpeta del altavoz para el que se quiere construir brutefir_config.
#       - La fs por defecto será 44100
#       - Debe existir un archivo '~/lspk/ALTAVOZ/brutefir_config.ini'.
#   - Se renombra a do_brutefir_config.py por claridad.
#   - Se adapta al abandono de la ubicación de PCMs para DRC en subcarpetas de la de audio
#   - Se adapta al cambio de nombre filters.ini --> filters.scan que refleja mejor la naturaleza de este archivo.
#   - Se mejora el algoritmo de elección de filtros pcm para construir la esctructura de filtrado.
#
"""
Construye un archivo 'brutefir_config' para FIRtro.

Uso:
    do_brutefir_config.py lskp/ALTAVOZ  [FS] [-w | -h]

        FS          fs por defecto 44100
        -w          escribe la salida en lspk/ALTAVOZ/FS/brutefir_config
        -h --help   muestra esta ayuda

El archivo 'brutefir_config' se construye en función de:

1) Un archivo de configuración 'lspk/ALTAVOZ/brutefir_config.ini' preparado
   por el USUARIO que especifica los parámetros necesarios:

    - La longitud y particionado de filtros, si se usa dither, etc

    - El MAPEO de entradas y salidas en JACK, así como la polaridad,
      atenuación y delays de las salidas.

2) La relación de pcms de filtrado que el USUARIO haya depositado
   en la carpeta de audio altavoz 'lspk/ALTAVOZ/FS'

Cada .pcm puede acompañarse de un .ini indicando la ganancia del FIR,
entonces se incorporará en la declaración 'coeff' correspondiente.

Este script hace uso del módulo 'scanfilters.py' que genera el archivo auxiliar
'lspk/ALTAVOZ/FS/filters.scan', con la clasificación de filtros pcm encontrados
en la carpeta del altavoz.

Se construirá una estructura de filtrado adecuada en función de los NOMBRES de
los archivos .PCM encontrados.

En caso de encontrar filtros 'sw' para subwoofer se incluirá una etapa de filtrado
a partir de la mezcla ponderada de los canales L y R.

Se priorizan los filtros 'lp' para construir la cadena de filtrado,
si no existieran se usarán los 'mp'.

---------------    REGLAS DE NOMBRADO de archivos pcm:    ---------------

Todos los .pcm admiten opcionalmente una cadena '_descriptivo' antes del sufijo '.pcm'

- pcms de DRC

    drc-N-C.pcm
    drc-N-C_descriptivo.pcm

    N: secuencial desde 1
    C: canal 'L' o  'R' al que va destinado

- pcms de VIAS ordinarias (separadas en cada canal)

    aa-bb.pcm
    aa-bb-C.pcm                 Opcional para dedicar el pcm a un CANAL
    aa-bb_descriptivo.pcm
    aa-bb-C_descriptivo.pcm

    aa: 'lp' 'mp'
    bb: 'hi' 'mi' 'lo' 'fr'     (fr indica "full range")
    C:  'L' 'R'                 (opcional)

- pcms de SUBWOOFER (recibirán la señal de todos los canales)

    aa-sw-ID.pcm
    aa-sw-ID_descriptivo.pcm

    aa: 'lp' 'mp'
    ID: identificador         (preferiblemente breve)

"""

import sys
from os import path as os_path
import ConfigParser
from numpy import log10 as np_log10
import scanfilters

HOME = os_path.expanduser("~")
sys.path.append(HOME + "/bin")
from basepaths import loudspeaker_folder
from getstatus import fs

def verificaEstructuraVias():
    ''' lee brutefir.ini
        devuelve: (viasCorrectas:boolean, VIAS:list)
    '''
    tiposDeVias = ["sw", "fr", "lo", "mi", "hi"]
    VIAS = []

    # validamos los nombres de vías del INI
    for viaINI in bf_ini.options("outputs"):
        if viaINI[:2] in tiposDeVias:
            if viaINI not in VIAS:
                # Compatibilidad con server_process: sufijo del canal en mayúscula.
                if not viaINI[:2] == 'sw':
                    viaINI = viaINI[:-1] + viaINI[-1].upper()
                VIAS.append(viaINI)
        else:
            print 'nombre de via incorrecto:', viaINI
            return False, [viaINI], False

    return True, VIAS

def hacer_CadenaConvolver(VIAS):

    print '\n# ------------------------------'
    print   '# --------  CONVOLVER   --------'
    print   '# ------------------------------'

    # EQ filtering:
    print '\n# --- EQ filtering:\n'
    for canal in CANALES:
        print 'filter "f_eq_' + canal + '" {'
        for input in bf_ini.options("inputs"):
            if input[-1].upper() == canal:
                print '    from_inputs:  "' + input[:-1] + input[-1].upper() + '";'
                print '    to_filters:   "f_drc_L", "f_drc_R" ;'
                print '    coeff:        "c_eq' + str(CANALES.index(canal)) +'";'
        print '};'

    # DRC filtering:
    print '\n# --- DRC filtering (se reciben los dos canales para poder hacer MONO):\n'
    for canal in CANALES:
        print 'filter "f_drc_' + canal + '" {'

        if canal == "L":
            print '    from_filters: "f_eq_L"//1, "f_eq_R"//0 ;'
        else:
            print '    from_filters: "f_eq_L"//0, "f_eq_R"//1 ;'

        # Ahora debemos llevar la señal a las VIAs y a los SUBs si existieran
        # tmp1 recoje las vias separadas por *canal*
        tmp1 = [ via for via in VIAS if '_' + canal in via ]
        tmp1 = [ x[:-1]+x[-1].upper() for x in tmp1]
        # tmp2 recoje los posibles *subwoofers*
        tmp2 = [via for via in VIAS if via[:2]=='sw' ]
        print '    to_filters:   "f_' + '", "f_'.join(tmp1 + tmp2) + '";'

        # podemos usar el primer DRC:
        # print '    coeff:        "c_drc1_' + canal + '";'
        # o podemos dejarlo plano a la espere de los scripts del FIRtro:
        print '    coeff:        -1;'

        print '};'

    # XOVER filtering:
    print '\n# --- XOVER filtering:\n'

    # 1. Agrupamos por canales
    for canal in CANALES:

        # (A) RECORREMOS las VIAS declaradas en 'brutefir_config.ini', las de este canal.
        # OjO 'via' en brutefir_config.ini es vv_ch o sea via+canal (abajo 'viacha')
        #     Aquí vamos a centrarnos en un canal para hacer la cadena de xover ordenada
        for via in [viacha[:2] for viacha in VIAS if canal == viacha[-1] ]:
            gain, polarity, delay = bf_ini.get("outputs", via+'_'+canal).split()[1:]

            # (B) RECORREMOS los coeffs listados en 'filters.scan'
            #
            #     Opcionalmente el .pcm podrá estar nombrado con el canal si es que se
            #     ubiera diseñado un filtrado diferenciado en alguna vía, ejemplo:
            #
            #     [lp_xo]
            #     c_lp-lo1 = ...../lp-lo_woofer.pcm
            #     c_lp-hi1 = ...../lp-hi-L_tweeter.pcm
            #     c_lp-hi2 = ...../lp-hi-R_tweeter.pcm
            #     ... etc ...

            # Priorizamos filtros lp
            if filters_ini.options('lp_xo'):
                inipha = 'lp_xo'
            else:
                inipha = 'mp_xo'

            matched = ''
            pcmPrioritario = False
            for coeff in filters_ini.options(inipha):
                pcm      = filters_ini.get(inipha, coeff).split("/")[-1]
                pcmvia   = pcm[3:5]
                pcmcan   = ''
                if pcm[5:7] == '-L':
                    pcmcan = 'L'
                if pcm[5:7] == '-R':
                    pcmcan = 'R'

                if pcmvia == via:
                    if pcmcan == canal:
                        pcmPrioritario = True
                        matched = coeff
                    # Se prioriza un pcm dedicado a un canal aunque apareciera otro genérico
                    elif not pcmcan and not pcmPrioritario:
                            matched = coeff

            print 'filter "f_' + via + "_" + canal + '" {'
            print '    from_filters: "f_drc_' + canal + '";'
            print '    to_outputs:   "' + via + '_' + canal + '"/' + gain + '/' + polarity + ';'

            if matched:
                print '    coeff:        "' + matched + '";'
            else:
                if via == 'fr':
                    print '    coeff:        -1;'
                else:
                    print '    coeff:        "COEFF NO ENCONTRADO PARA ESTA VIA";'
            print '};'

    # SUBWOOFER filtering
    if any(via for via in VIAS if via[:3]=='sw_' ):
        print '\n# --- SUB filtering:\n'

        # (A) RECORREMOS las vias de subwoofer declaradas en 'brutefir_config.ini'
        for via in [x for x in VIAS if x[:2] == 'sw']:

            gain, polarity, delay = bf_ini.get("outputs", via).split()[1:]
            mixAtt = '{:.2}'.format(-10 * np_log10(1.0/len(CANALES)))

            # (B) RECORREMOS los coeffs listados en 'filters.scan'

            # Priorizamos filtros lp
            if filters_ini.options('lp_sw'):
                inipha = 'lp_sw'
            else:
                inipha = 'mp_sw'

            matched = ''
            for coeff in filters_ini.options(inipha):
                pcm     = filters_ini.get(inipha, coeff).split("/")[-1]
                # ejemplos  via:     sw_amr     pcm:      lp-sw-amr_60Hz.pcm
                #                               pcm:      lp-sw-amr.pcm
                #                               pcmvia:   sw-amr
                #           viaswID:    amr     pcmswID:     amr
                pcmvia  = pcm [3:].replace('.pcm','').split("_")[0]
                pcmswID = pcmvia.split("-")[-1]
                viaswID = via.split("_")[-1]

                if pcmswID == viaswID:
                    matched = coeff

            print 'filter "f_' + via + '" {'
            tmp = '"f_drc_' + ('"/' + mixAtt + ', "f_drc_').join(CANALES) + '"/' + mixAtt +';'
            print '    from_filters: ' + tmp
            print '    to_outputs:   "' + via + '"/' + gain + '/' + polarity + ';'
            if matched:
                print '    coeff:        "' + matched + '";'
            else:
                print '    coeff:        "COEFF NO ENCONTRADO PARA ESTE SUBWOOFER";'
            print '};'

def hacer_IO():

    print '\n# -------------------------'
    print   '# --------  I/O -----------'
    print   '# -------------------------'

    # ENTRADAS (CANALES)
    tmp2 = '"in_' + '", "in_'.join(CANALES) + '"'
    print '\ninput ' + tmp2 + ' {'
    print '    # Sin conexiones a priori en la entrada:'
    print '    device: "jack" { };'
    print '    sample: "AUTO";'
    tmp = ','.join([str(x) for x in range(len(CANALES))])
    print '    channels: ' + str(len(CANALES)) + '/' + tmp + ';'
    print '};'

    # SALIDAS (VIAS)
    tmp = '", "'.join(VIAS)
    print '\noutput "' + tmp + '" {'
    print '    # mapeo de las ' + str(len(VIAS)) + ' salidas:'

    print '    device: "jack" { ports:'
    jackPorts = []
    for via in VIAS:
        jackPorts.append('"' + bf_ini.get("outputs", via).split()[0] + '"/"' + via + '"')

    # churro de puertos de salida organizado en dos columnas para legibilidad
    churro = '    '
    maxCols= 2
    col  = 1
    indicePuerto  = 0

    while indicePuerto <= len(jackPorts)-1:  # recorremos los puertos de salida
        if col > maxCols:
            churro += '\n    '
            col = 1
        churro += jackPorts[indicePuerto] + ', '
        indicePuerto += 1
        col += 1

    print churro[:-2] + ';' # el último ", " lo cerramos con ";"

    print '    };'

    print '    sample:   "AUTO";'
    tmp = ','.join([str(x) for x in range(len(VIAS))])
    print '    channels: ' + str(len(VIAS)) + '/' + tmp + ';'
    print '    maxdelay: 1000;'
    print '    dither:   ' + dither + ';'

    delaysMS= []
    for via in VIAS:
        delaysMS.append(bf_ini.get("outputs", via).split()[3])
    delaysSamples = [x.replace(x, str(int(int(fs)*float(x)/1000))) for x in delaysMS]
    print '    delay:    ' + ','.join(delaysSamples) + '; # \'samples\' that are equivalent in \'ms\' to ' \
          + ','.join(delaysMS)

    print '};'

def hacer_Coef_EQ():

    print '\n# --------------------------------'
    print   '# ----- EQ & LOUDNESS COEFFs -----'
    print   '# --------------------------------\n'

    for i in range(len(CANALES)):
        print 'coeff "c_eq' + str(i) + '" {'
        print '    filename: "dirac pulse";'
        print '    shared_mem: true;'
        print '    blocks: 1; # suficiente para hacer curvas de EQ suave'
        print '};'

def hacer_Coef_DRC():

    print '\n# --------------------------------'
    print   '# ---------- DRC COEFFs ----------'
    print   '# --------------------------------\n'

    for coeff in filters_ini.options("drcs"):
        gain = filters_ini.get("drcs", coeff).split()[0]
        file = ' '.join(filters_ini.get("drcs", coeff).split()[1:])

        # Compatibilidad con server_process: sufijo del canal en mayúscula.
        if not coeff[:2] == 'sw':
            coeff = coeff[:-1] + coeff[-1].upper()

        print 'coeff "' + coeff + '" {'
        print '    filename:    "' + file + '";'
        print '    format:      "FLOAT_LE";  shared_mem:  false;'
        print '    attenuation: ' + gain + ';'
        print '};'

def hacer_Coef_XO():

    print '\n# --------------------------------'
    print   '# ---------- XO COEFFs -----------'
    print   '# --------------------------------'

    listaTmp = []

    for type in ["lp", "mp"]:

        for coeff in filters_ini.options(type + "_xo"):

            tmp = ""
            gain = filters_ini.get(type + "_xo", coeff).split()[0]
            pcmfile = ' '.join(filters_ini.get(type + "_xo", coeff).split()[1:])
            tmp += 'coeff "' + coeff + '" {\n'
            tmp +=  '    filename:    "' + pcmfile + '";\n'
            tmp +=  '    format:      "FLOAT_LE";  shared_mem:  false;\n'
            tmp +=  '    attenuation: ' + gain + ';\n'
            tmp +=  '};'
            listaTmp.append(tmp)

        for coeff in filters_ini.options(type + "_sw"):

            tmp = ""
            gain = filters_ini.get(type + "_sw", coeff).split()[0]
            pcmfile = ' '.join(filters_ini.get(type + "_sw", coeff).split()[1:])
            tmp +=  'coeff "' + coeff + '" {\n'
            tmp +=  '    filename:    "' + pcmfile + '";\n'
            tmp +=  '    format:      "FLOAT_LE";  shared_mem:  false;\n'
            tmp +=  '    attenuation: ' + gain + ';\n'
            tmp +=  '};'
            listaTmp.append(tmp)

    #v1.2a se reagrupan por el nombre del coeff para mejor visibilidad de las atenuaciones.
    listaTmp = sorted(listaTmp, key=lambda x: (x[12:]), reverse=False)
    cosaprev = ""
    for cosa in listaTmp:
        if not cosa[12:17] in cosaprev:
            print
        print cosa
        cosaprev = cosa


    print '\n# coeficiente comodín para vias full range sin filtrado'
    print 'coeff "' + 'c_dirac-pulse' + '" {'
    print '    filename:    "' + 'dirac pulse' + '";'
    print '    format:      "FLOAT_LE";  shared_mem:  false;'
    print '    attenuation: ' + '0.0' + ';'
    print '};'

def lee_secc_gral(param):
    """ arreglo para permitir que la seccion [general] de brutefir.ini
        pueda escribirse con ';' y '#' (comentarios) al modo de brutefir_bf_ini.
    """
    return bf_ini.get("general", param ).split(';')[0].split('#')[0].strip().lower()

def hacer_cabecera():
    print '# --------------------------------------------------'
    print '#    GENERADO POR do_brutefir_config.py BASADO EN:'
    print '#    ' + bf_ini_file
    print '# --------------------------------------------------'
    print
    print '# ------------------------------'
    print '# ------ GENERAL SETTINGS ------'
    print '# ------------------------------\n'

    print 'sampling_rate:     ' + str(int(fs)) + ';\n'

    print 'filter_length:     ' + lee_secc_gral("filter_length")     + ';'
    print 'float_bits:        ' + lee_secc_gral("float_bits")        + ';\n'

    print 'overflow_warnings: ' + lee_secc_gral("overflow_warnings") + ';'
    print 'allow_poll_mode:   ' + lee_secc_gral("allow_poll_mode")   + ';'
    print 'monitor_rate:      ' + lee_secc_gral("monitor_rate")      + ';'
    print 'powersave:         ' + lee_secc_gral("powersave")         + ';'
    print 'lock_memory:       ' + lee_secc_gral("lock_memory")       + ';'
    print 'show_progress:     ' + lee_secc_gral("show_progress")     + ';'

#------------------------------------------ MAIN -----------------------------------------
if __name__ == "__main__":

    salidaPorConsola = True

    # Preparamos la estructura de variables
    bf_ini      = ConfigParser.ConfigParser()
    filters_ini = ConfigParser.ConfigParser()
    avisos      = []
    loudspeaker = ''
    fs          = '44100' # por defecto

    # Leemos argumentos:
    if sys.argv[1:]:

        args = sys.argv[1:]

        # se pide ayuda
        tmp = [ x for x in args if "-h" in x ]
        if tmp:
            print __doc__
            sys.exit(0)

        # si se pide escritura de la salida
        if "-w" in args:
            salidaPorConsola = False
        else:
            salidaPorConsola = True

        # altavoz
        tmp = [ x for x in args if "lspk/" in x ]
        if tmp:
            loudspeaker = tmp[0].split("lspk/")[1].replace("/", "") # por si se pasara con el slash final

        # fs
        tmp = [ x for x in args if x.isdigit() ]
        if tmp:
            fs = tmp[0]

    else:
        print "(!) Indicar lspk/ALTAVOZ o -h para ayuda"
        sys.exit(0)

    # Carpeta de audio:
    audio_folder     = loudspeaker_folder + loudspeaker + "/" + fs
    if not os_path.isdir(audio_folder):
        print "(!) NO existe '" + audio_folder + "'"
        sys.exit()

    bf_ini_file      = loudspeaker_folder + loudspeaker + "/brutefir_config.ini"

    if os_path.exists(bf_ini_file):
        bf_ini.read(bf_ini_file)
    else:
        print "(!) NO existe '" + bf_ini_file + "'"
        sys.exit()

    dither = lee_secc_gral("dither")

    CANALES = []
    for input in bf_ini.options("inputs"):
        if not input[-1] in CANALES:
            CANALES.append(input[-1].upper()) # mayúscula por compatibilidad con FIRtro original

    viasCorrectas, VIAS  = verificaEstructuraVias()

    if viasCorrectas:
        avisos.append('\n(i) Se ha validado la configuracion de vías.')

        # scanfilters genera filters.scan con los filtros encontrados en la carpeta del altavoz.
        scanfilters.main(audio_folder)
        filters_ini_file = audio_folder + "/filters.scan"
        filters_ini.read(filters_ini_file)

        # Ahora generamos brutefir_config a partir de brutefir.ini y filters.scan

        # // redirigimos el printado a fichero si así se requiriera
        # memorizamos la stdout original (la consola)
        original_stdout = sys.stdout
        if not salidaPorConsola:
            sys.stdout = open(audio_folder + "/brutefir_config", "w")
        hacer_cabecera()
        hacer_IO()
        hacer_Coef_EQ()
        hacer_Coef_DRC()
        hacer_Coef_XO()
        hacer_CadenaConvolver(VIAS)
        sys.stdout = original_stdout
        # \\ ^^^ recuperamos el printado por consola

        print "\n--------------------------------------------------------"
        print   "(i) Atención:"
        if salidaPorConsola:
            print "\n(i) Se ha leido:", bf_ini_file
            print "\n(i) Se han buscado pcms en:", loudspeaker_folder + loudspeaker + "/" + str(int(fs))
            print "\n(!) Usar la opción -w para guardar en:"
            print "\n        " + audio_folder + "/brutefir_config"
        else:
            print "\n(i) Se ha guardado " + audio_folder + "/brutefir_config\n"

    else:
        avisos.append('la estructura de puertos de salida en brutefir.ini no es correcta')

    for aviso in avisos:
        print aviso
    print "\nBye!"

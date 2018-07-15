#!/usr/bin/env python
# -*- coding: utf-8 -*-

# v1.0: se permite argumento "-w" para escribir la salida en el archivo brutefir_config
# v1.1: incorpora un coeff de xover "dirac pulse" para poder cargarlo en una vía full range"
# v1.2: se permiten nuevos argumentos:
#     - un archivo brutefir.ini alternativo
#     - una carpeta de altavoz distinta de la configurada en el sistema en audio/config
# v1.2a: los coeff de cruce se dejan de agrupar primero lp y luego mp,
#        se printan por parejas lp/mp para mejor visibilidad de las atenuaciones de cada coeff.

### ESTE SCRIPT ES MUY RUDIMENTARIO HABRIA QUE REESCRIBIRLO :-/
### INCLUYENDO EL SCANEO DE PCMs Y TAL ...


"""
Uso:
    brutefir_config.py opciones

    opciones:
        /path/to/'brutefir.ini'file   (obligatorio)
        /path/to/lskp/altavoz         (por defecto el configurado en ~/audio/config)
        -w                            escribe la salida en el archivo brutefir_config
        -h --help                     muestra esta ayuda

Este script de usuario construye un archivo "brutefir_config" en función de:

1) Un archivo de configuración básica ~/audio/brutefir.ini que especifica parámetros generales:
    - la longitud y particionado de filtros, si se usa dither, etc
    - el mapeo de entradas y salidas en JACK, así como la polaridad,
      atenuación y delays de las salidas.

2) La relación de pcms de filtrado que se encuentre en la carpeta del altavoz. Cada "xxxxxx.pcm"
   debe acompañarse de un "xxxxxx.ini" que contiene la ganancia del filtro (a modo de metadato
   en archivo paraleleo) para ser tenida en cuenta a la hora de declarar los coeff en brutefir_config.

Este script hace uso del módulo scanfilters.py que genera el archivos auxiliar
"~/lspk/altavoz/Fs/filters.ini", con la clasificación de filtros pcm encontrados
en la carpeta del altavoz.

En función de los nombres de archivos de filtro encontrados, se construirá una estructura de
filtrado adecuada.

Los nombres de los archivos de filtrado deben acomodarse a:

    aa-bb_nombre_descriptivo.pcm  (sin espacios)

    siendo:
    aa: 'mp' 'lp'
    bb: 'hi' 'mi' 'lo' 'sw' 'fr'  (fr es indicativo de que se ecualiza una caja pasiva "full range")

En caso de encontrar filtros "sw" para subwoofer se incluirá una etapa de filtrado a partir
de la mezcla ponderada de los canales L y R provinientes de la etapa de drc, la misma etapa
que proporciona la señal a las etapas de filtrado de vías.

NOTA: en caso de existir varios pcm para una misma vía, se asignará el primero listado
en el archivo filters.ini que se menciona arriba.
Si se desea cargar un pcm determinado, se debe de hacer un cambio al vuelo mediante el CLI de Brutefir
o bien nombrar el archivo con un orden alfabético menor.

"""

import sys
from os import path as os_path
import ConfigParser
from numpy import log10 as np_log10
import scanfilters

HOME = os_path.expanduser("~")
sys.path.append(HOME + "/bin")
from basepaths import loudspeaker_folder
from getconfig import loudspeaker
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
                # por compatibilidad ponemos el sufijo del canal en mayúscula.
                VIAS.append(viaINI[:-1] + viaINI[-1].upper())
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
                print '    to_filters:   "f_drc_' + canal + '";'
                print '    coeff:        "c_eq' + str(CANALES.index(canal)) +'";'
        print '};'

    # DRC filtering:
    print '\n# --- DRC filtering:\n'
    for canal in CANALES:
        print 'filter "f_drc_' + canal + '" {'
        print '    from_filters: "f_eq_' + canal + '";'

        # Ahora debemos llevar la señal a las VIAs y a los SUBs si existieran
        # tmp1 recoje las vias separadas por canal
        tmp1 = [via for via in VIAS if '_' + canal in via]
        tmp1 = [x[:-1]+x[-1].upper() for x in tmp1]
        # tmp2 recoje los posibles subwoofers
        tmp2 = [via for via in VIAS if 'sw' in via]
        tmp2 = [x[:-1]+x[-1].upper() for x in tmp2]
        print '    to_filters:   "f_' + '", "f_'.join(tmp1 + tmp2) + '";'

        # podemos usar el primer DRC:
        # print '    coeff:        "c_drc1_' + canal + '";'
        # o podemos dejarlo plano a la espere de los scripts del FIRtro:
        print '    coeff:        -1;'

        print '};'

    # XOVER filtering:
    print '\n# --- XOVER filtering:\n'
    for canal in CANALES:
        for via in [x for x in VIAS if '_' + canal in x]:
            gain, polarity, delay = bf_ini.get("outputs", via).split()[1:]
            print 'filter "f_' + via + '" {'
            print '    from_filters: "f_drc_' + canal + '";'
            print '    to_outputs:   "' + via + '"/' + gain + '/' + polarity + ';'

            # busquemos el primer coeff disponible para la via en filters.ini
            for option in filters_ini.options('lp_xo'):
                if option[5:7] == via[:2]:  # ej: fr_l ---> fr
                    break
            print '    coeff:        "' + option + '";'

            print '};'

    # SUBWOOFER filtering
    if any(via for via in VIAS if 'sw' in via):
        print '\n# --- SUB filtering:\n'

        for via in [x for x in VIAS if 'sw' in x]:

            gain, polarity, delay = bf_ini.get("outputs", via).split()[1:]
            mixAtt = '{:.2}'.format(-10 * np_log10(1.0/len(CANALES)))

            print 'filter "f_' + via + '" {'
            tmp = '"f_drc_' + ('"/' + mixAtt + ', "f_drc_').join(CANALES) + '"/' + mixAtt +';'
            print '    from_filters: ' + tmp
            print '    to_outputs:   "' + via + '"/' + gain + '/' + polarity + ';'

            # busquemos el primer coeff disponible para la via en filters.ini
            for option in filters_ini.options('lp_sw'):
                if option[5:7] == via[:2]:  # ej: fr_l ---> fr
                    break
            print '    coeff:        "' + option + '";'

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
    delaysSamples = [x.replace(x, str(int(fs*float(x)/1000))) for x in delaysMS]
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
            # por compatibilidad mayuscula al final
            tmp = coeff[:-1] + coeff[-1].upper()
            print 'coeff "' + tmp + '" {'
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

if __name__ == "__main__":

    salidaPorConsola = True

    #preparamos la estructura de variables
    bf_ini      = ConfigParser.ConfigParser()
    filters_ini = ConfigParser.ConfigParser()
    avisos      = []

    # el archivo brutefir.ini es obligatorio como argumento.
    bf_ini_file = ""
    # ubicación por defecto de la carpeta del altavoz
    audio_folder = loudspeaker_folder + loudspeaker + "/" + fs

    # si se pasan argumentos los atendemos
    if sys.argv[1:]:
        args = sys.argv[1:]

        # si se pide escritura de la salida
        if "-w" in args:
            salidaPorConsola = False
        else:
            salidaPorConsola = True

        # archivo brutefir.ini
        tmp = [x for x in args if ".ini" in x and "/" in x]
        if tmp:
            bf_ini_file = tmp[0]

        # si se indica una carpeta de altavoz en particular
        # OjO debe proporcionarse como "lspk/otroAltavoz"
        tmp = [x for x in args if "lspk/" in x]
        if tmp:
            loudspeaker = tmp[0].split("lspk/")[1]

        # se pide ayuda
        tmp = [x for x in args if "-h" in x]
        if tmp or not bf_ini_file:
            print __doc__
            sys.exit(0)

    else:
        print __doc__
        sys.exit(0)


    audio_folder = loudspeaker_folder + loudspeaker + "/" + fs
    filters_ini_file = audio_folder + "/filters.ini"

    bf_ini.read(bf_ini_file)
    filters_ini.read(filters_ini_file)

    # lee y verifica brutefir.ini
    fs     = float(lee_secc_gral("fs"))
    dither = lee_secc_gral("dither")

    CANALES = []
    for input in bf_ini.options("inputs"):
        if not input[-1] in CANALES:
            CANALES.append(input[-1].upper()) # mayúscula por compatibilidad con FIRtro original

    viasCorrectas, VIAS  = verificaEstructuraVias()

    if viasCorrectas:
        avisos.append('\n(i) Se ha validado la configuracion de vías.')

        # scanfilters genera filters.ini con los filtros encontrados en la carpeta del altavoz.
        scanfilters.main(audio_folder)

        # Ahora generamos brutefir_config a partir de brutefir.ini y filters.ini

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
            print "\n(i) Se ha leido:", loudspeaker_folder + loudspeaker + "/" + str(int(fs))
            print "\n(!) Usar la opción -w para guardar en:"
            print "\n        " + audio_folder + "/brutefir_config"
        else:
            print "\n(i) Se ha guardado " + audio_folder + "/brutefir_config\n"
            print "\n(i) creando symlinks a las carpetas drc-x ... ...\n"
            import drc_generate_symlinks
            drc_generate_symlinks.main(audio_folder)

    else:
        avisos.append('la estructura de puertos de salida en brutefir.ini no es correcta')

    for aviso in avisos:
        print aviso
    print "\nBye!"
    print "\n(i) OjO VERSION EN PRUEBAS admite configuraciones FR + VIAS + SUB altogether\n"

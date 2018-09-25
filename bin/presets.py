#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    FIRtro 2.0 Módulo de gestión de presets usado por server_process.
    Uso en línea de comando:
        presets.py  list        listado de presets disponibles
                    nombre      detalla los presets que coincidan
                    #número     carga un preset del listado
                                sin argumentos muestra preset actual
"""
# v1.1:
# - Permite indicar "dirac_pulse" en vías full range (en ese caso no existe un pcm real).
# v1.2
# - Gestiona PEQ (EQ paramétrico basado en Ecasound).
# v1.3:
# - Se incorpora la atenuacion y el delay para cada vía.
# v1.3b
# - Se simplifica el archivo presets.ini con el nombre descriptivo del preset en la propia sección INI.
# - Se implementa línea de comandos para búsquedas.
# v1.3c
# - Se deja de usar nc localhost para hablar con Brutefir, ahora usamos el cliente brutefir_cli.py
# - Se continuá la ejecución en caso de que Brutefir no esté accesible
# v1.3d
# - Se amplían las opciones por línea de comandos
# v2.0a
# - Se reescriben las funciones de configuracion y activación de las vias:
#   Se distingue cada canal, se optimiza el código.
# - Se adapta para manejar distintos subwoofers
# - Se usa RawConfigParser + .optionxform = str para preservar nombres de vias case sensitive en presets.ini
# v2.1
# - Reubicación de los pcm de DRC en la carpeta original audio_folder (lspk/altavoz/FS)
# - Se comprueba que cada vía a configurar se corresponda con uno de los coeff disponibles en Brutefir.

import brutefir_cli
from subprocess import Popen
import os
from sys import path as sys_path, argv as sys_argv, exit as sys_exit
import socket
import ConfigParser

# para conectar solo las salidas de brutefir de las VIAS EN USO a la tarjeta de sonido
import jack

# El módulo "read_brutefir_process.py" proporciona la relación de coeficientes
# cargados en Brutefir y los filtros con los coeficientes que tienen asignados,
# y tambien proporciona el mapeo de salidas de Brutefir en Jack
import read_brutefir_process  as brutefir
# rev 1.3c:
brutefir.outputsMap = []
brutefir.coeffs = []
brutefir.filters_at_start = []
brutefir.filters_running = []

# Para que funcione la cosa actualizamos las listas:
bferror = False
try:   
    brutefir.lee_config()
except:
    bferror = True
try:
    brutefir.lee_running_config()
except:
    bferror = True
if bferror:
    print "(presets.py) No se ha podido comunicar con Brutefir"

# modulos del FIRtro:
HOME = os.path.expanduser("~")
sys_path.append(HOME + "/bin")
from basepaths import loudspeaker_folder, config_folder
from getconfig import loudspeaker
from getstatus import drc_eq as drc_status

status = ConfigParser.ConfigParser()
status.read(config_folder + "/status")
# carpeta del altavoz/fs
altavoz_folder = loudspeaker_folder + loudspeaker

# archivo de definición de nuestros presets para este altavoz:
presets = ConfigParser.RawConfigParser()
presets.optionxform = str
presets.read(altavoz_folder + "/presets.ini")
# recopilador de avisos para printar
avisos = []

def configura_preset(presetID, filter_type):
    """ Esta función se encarga de configurar en el proceso brutefir el coeff de los xover
        y subwoofer si procede, como se haya definido en el archivo de presets de usuario.
        Y devuelve los siguientes valores a server_process para que se actualize en el sistema:
        - la descripción del preset
        - el numero de drc requerido
        - la configuración de PEQ
        - el ajuste de balance
    """
    global avisos
    
    if presets.has_section(presetID):
        avisos += [ "(presets) Ha seleccionado preset: " + presetID ]
        avisos += [ "\n                                        ftype:\taten:\tdelay:\tpcm:" ]
        viasDelPreset = []
        etiquetasDeVias = ["fr", "lo", "mi", "hi", "sw"]

        # [presetID]
        # opcion1 = valor1
        # opcion2 = valor2
        # ...     = ...... 
        # etc
        for opcion in presets.options(presetID):
            valor = presets.get(presetID, opcion)

            # opciones del ini relativas a DRC:
            if opcion in ["drc"]:
                drc_num = configura_drc_coeff(valor)

            # opciones del ini relativas a VÍAS:
            if [x for x in etiquetasDeVias if x in opcion]:
                via = opcion # solo para legibilidad
                atten, delay, pcm_name = valor.split()
                if configura_via(via, atten, delay, pcm_name, filter_type):
                    viasDelPreset.append(via)
                    avisos += [ "(presets) Se configura la via: \t" \
                                + via + "\t" + filter_type + "\t" + atten + "\t" + delay + "\t" + pcm_name ]
                else:
                    avisos += [ "(presets) ERROR en la via:     \t" + via + "\t\t(revisar pcm en presets.ini)" ]
                    

            # opciones del ini relativas a BALANCE:
            if opcion in ["balance"]:
                balance = ajusta_balance(valor)

            # opciones del ini relativas a PEQ:
            if opcion in ["peq"]:
                peq = ajusta_peq(valor)

        avisos += ["(presets) Enjoy!\n"]
        # Conectamos a la tarjeta solo las vias definidas en el preset:
        conecta_tarjeta(viasDelPreset)

    else:
        presetID = "ERROR PRESET NO VALIDO"
        drc_num = drc_status
        balance = "0"
        peq = None

    for aviso in avisos:
        print aviso
    avisos = []

    return presetID, drc_num, balance, peq

def busca_preset(presetID):
    if presets.has_section(presetID):
        return presetID
    else:
        return None

def ajusta_balance(balance):
    # para ajustar el balance hay que hablar con el FIRtro para que quede reflejado en la web y en status
    # o sea que esta función no hace nada :-)
    return balance

def ajusta_peq(peq):
    # para ajustar el PEQ hay que hablar con el FIRtro para que quede reflejado en la web y en status
    # o sea que esta función no hace nada :-)
    return peq

def configura_drc_coeff(fName):
    """ funcion auxiliar para cargar el drc del preset seleccionado
        devuelve una string con el índice del coeff drc que se pretende cargar,
        que es lo que entiende server_process
    """
    global avisos
    
    if fName == 'off':
        avisos += ["(presets) Se configura drc num:\t0\t\t\t\t-1 (off)" ]
        return "0"

    drc_nums_found = []
    # Recorremos los coeff de drc disponibles en brutefir_config
    drc_coeffs = [x for x in brutefir.coeffs if x[1][:5]=="c_drc"] # filtramos los coeff de drc
    for x in drc_coeffs:
        # OjO coeff_num es la posicion que ocupa dentro de todos los coeff declarados
        #     en brutefir_config, NO confundir con el drc_num (el índice de los drc disponibles).
        coeff_num, coeff_name, pcm_file = x
        drc_num = coeff_name[5]
        drc_channel = coeff_name[-1]
        # ejemplo pcm_file: 'drc-1-L xxxxxxxxxx.pcm"
        bare_pcm_file = pcm_file[7:-4].strip()
        if bare_pcm_file == fName:
            drc_nums_found.append(drc_num)

    # Veamos si todos los drc_num son el mismo:
    if drc_nums_found and drc_nums_found.count(drc_nums_found[0]) == len(drc_nums_found):
        avisos += ["(presets) Se configura drc num:\t" + drc_nums_found[0] + "\t\t\t\t" + fName ]
        return drc_nums_found[0]
    else:
        avisos += ["(presets) algo no ha ido bien localizando el drc :-/"]
        return "0"

def configura_via(via, atten, delay, pcmName, filter_type):
    """ Funcion auxiliar para cargar en Brutefir el filtro de xover
        definido en el preset seleccionado.
        NOTA:   Se ha convenido que presets.ini no incluya el prefigo 'lp-'/'mp-'
                ni la extensión '.pcm'
    """
    atten = str(float(atten))
    samples = str(int(float(delay)/1000*44100))
    if "dirac" in pcmName:
        pcmName = "dirac pulse"
    else:
        pcmName = filter_type + "-" + pcmName + ".pcm"

    # Recorremos los coeff disponibles en Brutfir,
    # saltamos los dos primeros que son de la etapa de EQ.
    matched = False
    for bfirCoeff in brutefir.coeffs[2:]:

        coeffNum, coeffName, coeffPcm = bfirCoeff
        
        if pcmName == coeffPcm:
            matched = True
            
            bfilter = "f_" + via

            # 1) carga el coeff:    cfc <filter> <coeff>
            tmp = 'cfc "' + bfilter + '" "' + coeffName + '"; quit;'
            brutefir_cli.bfcli(tmp)

            # 2) ajusta la atten:   cfoa <filter> <output> <attenuation>
            tmp = 'cfoa "' + bfilter + '" "' + via + '" ' + atten + '; quit;'
            brutefir_cli.bfcli(tmp)

            # 3) ajusta el delay:   cod <output> <delay>
            tmp = 'cod "' + via + '" ' + samples + '; quit;'
            brutefir_cli.bfcli(tmp)

    if matched:
        return True
    else:
        return False

def conecta_tarjeta(vias):

    jack.attach("tmp")

    # Disponemos de la funcion brutefir.outputsMap que contiene 
    # el mapeo de vias tal como esta definido en brutefir_config, por ejemplo:
    #   system:playback_3/hi_L
    #   system:playback_4/hi_R
    #   system:playback_7/lo_L
    #   system:playback_8/lo_R
    #   system:playback_5/sw1
    #   system:playback_6/sw2

    to_disconnect=[]
    to_connect = []
    
    # Ahora debemos evaluar si es una salida a activar:
    for bfOutMap in brutefir.outputsMap:
        conectar = False
        jackDest, bfOut = bfOutMap.split('/')
        jackOrig        = "brutefir:" + bfOut

        for via in vias:
            if via.lower() in bfOut.lower():
                conectar = True

        if conectar:
            to_connect.append( (jackOrig, jackDest) )
        else:
            to_disconnect.append( (jackOrig, jackDest) )
    
    for pair in to_disconnect:
        jack.disconnect(pair[0], pair[1])
    for pair in to_connect:
        jack.connect(pair[0], pair[1])

    jack.detach()

# OjO no simplificar, usado en server_process para pasarla a la web via json
def lista_de_presets():
    """ devuelve la lista de presets
    """
    return presets.sections()

# Solo para uso en la línea de comandos
def printa_presets(x=''):
    """ muestra los presets definidos en el archivo presets.ini del altavoz
    """
    if x in ("all", "list") or "-l" in x:
        i = 0
        for preset in presets.sections():
            i += 1
            print str(i) + ":", preset

    else:
        print
        for preset in lista_de_presets():
            if x in preset:
                print "[" + preset + "]"
                print "via:".ljust(12), " ".ljust(4), "atten delay   filtro"
                for option in presets.options(preset):
                    print option.ljust(12), "=".ljust(4), presets.get(preset, option)
            print

# Uso en la línea de comandos
if __name__ == '__main__':

    if sys_argv[1:]:
        opc = sys_argv[1]

        # Ayuda
        if "-h" in opc:
            print __doc__
            sys_exit(0)

        # Selecciona un preset
        elif opc.isdigit():
            i = 0
            for preset in presets.sections():
                i += 1
                if int(opc) == i:
                    print "(presets) Configurando preset: " + preset
                    Popen("control preset " + preset, shell=True)

        # lista de presets
        else:
            printa_presets(opc)

    # sin argumentos muestra el preset configurado
    else:
        Popen("grep preset /home/firtro/audio/status", shell=True)

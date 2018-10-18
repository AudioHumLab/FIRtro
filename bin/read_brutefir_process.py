#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    Módulo interfaz con Brutefir, usado por el módulo presets.py,
    también funciona en línea de comandos.

    Se lee brutefir_config y se conecta con el proceso brutefir.

    Se proporcionan CUATRO listas:

    outputsMap: lista de salidas y su correspondiente puerto en JACK.
    coeffs: lista de coeficientes disponibles.
    filters_at_start: lista de filtros con los coeficientes definidos en la carga de Brutefir.
    filters_running: lista de filtros con los coeficientes en curso.

    Cada uno de los coeff y de los filtros son diccionarios
"""

# v1: se printa
# - la colección de coeficientes disponibles en brutefir
# - la configuracion de filtros/coeff definida en brutefir_config
# - la configuración de filtros/coeff actual que corre en el proceso brutefir
# v2:
# - printa el mapeo de salidas de brutefir
# - printa las conexiones de brutefir en jack
# v2.1
# - contempla la existencia de coeff "dirac pulse" para vias full range sin filtrar
# v2.1a
# - Se deja de usar nc localhost en favor de brutefir_cli.py
# v2.1b
# - Se quitan las comillas en el mapeo de salidas, y se renombra la lista 'outputsMap' para mejor claridad.
# v2.2
# - Se simplifica el código
# - Se usan diccionarios para los coeff y los filtros
# - Se incluyen las attenuation de los coeff, y en los filters la atten y la polaridad en to_output:

import sys, os
import subprocess
import jack_conexiones as jc
import brutefir_cli

HOME = os.path.expanduser("~")

# algunos modulos del FIRtro
sys.path.append(HOME + "/bin")
from basepaths import loudspeaker_folder
from getconfig import loudspeaker
from getstatus import fs

audio_folder = loudspeaker_folder + loudspeaker + "/" + fs
brutefir_config = audio_folder + "/brutefir_config"


def read_config():
    """ se ocupa de leer outputsMap, coeffs, filters_at_start
    """
    global outputsMap, coeffs, filters_at_start

    f = open(brutefir_config, 'r')
    lineas = f.readlines()

    # Outputs storage
    outputIniciado = False
    outputsTmp= ''
    outputsMap = []

    # Coeff storage
    coeffIndex = -1
    coeffIniciado = False
    coeffs = []

    # Filters Storage
    filterIndex = -1
    filterIniciado = False
    filters_at_start = []

    # Bucle de lectura de brutefir.config (linea a linea)
    for linea in lineas:

        #######################
        # Leemos las OUTPUTs
        #######################
        if linea.startswith("output"):
            outputIniciado = True

        if outputIniciado:
            outputsTmp += linea.strip()
            if "}" in linea: # fin de la lectura de las outputs
                outputIniciado = False
                outputsTmp = outputsTmp.split("ports:")[1].split(";")[0].replace(" ", "")
                outputsTmp = outputsTmp.replace('"', '')
                outputsMap = outputsTmp.split(",")

        #######################
        # Recopilamos COEFFs
        #######################
        if linea.startswith("coeff"):
            coeffIniciado = True
            coeffIndex +=1
            cName = linea.split('"')[1].split('"')[0]

        if coeffIniciado:
            if "filename:" in linea:
                pcm = linea.split('"')[1].split('"')[0].split("/")[-1]
            if "attenuation:" in linea:
                cAtten = linea.split()[-1].replace(';','').strip()
            if "}" in linea:
                try:
                    coeffs.append( {'index':str(coeffIndex), 'name':cName, 'pcm':pcm, 'atten':cAtten} )
                except:
                    coeffs.append( {'index':str(coeffIndex), 'name':cName, 'pcm':pcm, 'atten':'0.0'} )
                coeffIniciado = False


        #######################################
        # Recopilamos las etapas de FILTRADO
        #######################################
        if linea.startswith("filter "):
            filterIniciado = True
            filterIndex +=1
            fName = linea.split('"')[1].split('"')[0]

        if filterIniciado:
            if "coeff:" in linea:
                cName = linea.split(':')[1].strip().replace('"', '').replace(";","")
            if "to_outputs" in linea:
                fAtten = linea.split("/")[-2]
                fPol = linea.split("/")[-1].replace(";","")
            if "}" in linea:
                filters_at_start.append( {'index':filterIndex, 'name':fName, 'coeff':cName} )
                filterIniciado = False


def read_running():
    """ lee los filtros que hay corriendo en Brutefir
    """
    global filters_running
    filters_running = []
    findex = -1

    ###########################################################
    # Obtenemos los filters_running (comando 'lf' en Brutefir)
    ###########################################################
    printado = brutefir_cli.bfcli("lf; quit")

    for linea in printado.split("\n"):
        atten = ''
        pol   = ''
        if ': "' in linea:
            findex += 1
            fname = linea.split('"')[-2]
        if "coeff set:" in linea:
            cset = linea.split(":")[1].split()[0]
        if "to outputs:" in linea:
            # NOTA: Se asume que se sale a una única output.
            #       Podría no ser cierto en configuraciones experimentales que 
            #       mezclen vías sobre un mismo canal de la tarjet de sonido
            if linea.strip() <> "to outputs:":
                if linea.count('/') == 2:
                    pol   = linea.split('/')[-1].strip()
                    atten = linea.split('/')[-2].strip()
                else:
                    pol   = '1'
                    atten = linea.split('/')[-1].strip()
            # El caso de las etapas eq y drc que no son salidas finales.
            else:
                pol   = '1'
                atten = '0.0'

            filters_running.append( {'index':str(findex), 'fname':fname, 'cset':cset, 'atten':atten, 'pol':pol} )

    #####################################
    # Cruzamos los filters con los coeff
    #####################################
    # Tenemos los nombres de los filtros con el número de coeficiente cargado en cada filtro,
    # ahora añadiremos el nombre del coeficiente y el pcm
    for frun in filters_running:
        for coeff in coeffs:
            if frun['cset'] == coeff['index']:
                frun['cname']  = coeff['name']
                frun['pcm']    = coeff['pcm']
                frun['catten'] = coeff['atten']


def main():
    """ printa coeffs, filters_running, mapeo de salidas y salidas conectadas
    """

    read_config()

    read_running()

    ################################
    print "\n--- Outputs map:"
    ################################
    for output in outputsMap:
        print output

    ################################
    print "\n--- Coeffs available:\n"
    ################################
    print "                             coeff# coeff           coeffAtten pcm_name"
    print "                             ------ -----           ---------- --------"
    for c in coeffs:
        a = '{:+6.2f}'.format( float(c['atten']) )
        print " "*29 + c['index'].rjust(4) +"   "+ c['name'].ljust(16) + a.ljust(11) + c['pcm']

    ################################
    print "\n--- Filters Running:\n"
    ################################
    print "fil# filterName  atten pol   coeff# coeff           coeffAtten pcm_name"
    print "---- ----------  ----- ---   ------ -----           ---------- --------"
    for f in filters_running:
        fa = '{:+6.2f}'.format( float(f['atten']) )
        ca = '{:+6.2f}'.format( float(f['catten']) )
        print f['index'].rjust(4) +" "+ f['fname'].ljust(11) + fa + f['pol'].rjust(4) + \
              f['cset'].rjust(7) +"   "+ f['cname'].ljust(16) + ca.ljust(11) + f['pcm']

    print "\n--- Jack:"
    for x in jc.jackConexiones("brutefir", "*"):
        print x[0].ljust(30) + x[1].ljust(8) + x[2]

    print


if __name__ == "__main__" :

    main()

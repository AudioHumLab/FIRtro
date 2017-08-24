#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    Módulo interfaz con Brutefir, usado por el módulo presets.py,
    también funciona en línea de comandos.
    
    Se lee brutefir_config y se conecta con el proceso brutefir.
    
    Se proporcionan CUATRO listas:
    outputs: lista de salidas y su correspondiente puerto ej JACK.
    coeffs: lista de coeficientes disponibles.
    filters_at_start: lista de filtros con los coeficientes definidos en la carga de Brutefir.
    filters_running: lista de filtros con los coeficientes en curso.

    v1: se printa
    - la colección de coeficientes disponibles en brutefir
    - la configuracion de filtros/coeff definida en brutefir_config
    - la configuración de filtros/coeff actual que corre en el proceso brutefir
    v2:
    - printa el mapeo de salidas de brutefir
    - printa las conexiones de brutefir en jack
    v2.1
    - contempla la existencia de coeff "dirac pulse" para vias full range sin filtrar
    v2.1a
    - se deja de usar nc localhost en favor de brutefir_cli.py
"""

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

def lee_config():
    """
    """

    f = open(brutefir_config, 'r')
    lineas = f.readlines()

    # Outputs storage
    outputIniciado = False
    global outputs
    outputsTmp= ''
    outputs = []

    # Coeff storage
    coeffIndex = -1
    coeffIniciado = False
    c_eqIniciado = False
    c_drcIniciado = False
    c_lpIniciado = False
    c_mpIniciado = False
    c_diracIniciado = False
    global coeffs
    coeffs = []

    # Filters Storage
    filterIndex = -1
    filterIniciado = False
    f_eqIniciado = False
    f_drcIniciado= False
    f_frIniciado = False
    f_loIniciado = False
    f_miIniciado = False
    f_hiIniciado = False
    f_swIniciado = False
    global filters_at_start
    filters_at_start = []

    # Bucle de lectura de brutefir.config (linea a linea)
    for linea in lineas:

        # Leemos las OUTPUTs
        if linea.startswith("output"):
            outputIniciado = True
        
        if outputIniciado:
            outputsTmp += linea.strip()
            if "}" in linea: # fin de la lectura de las outputs
                outputIniciado = False
                outputsTmp = outputsTmp.split("ports:")[1].split(";")[0].replace(" ","")
                outputs = outputsTmp.split(",")

        # Recopilamos COEFFs
        if linea.startswith("coeff"):
            coeffIniciado = True
            coeffIndex +=1
            cName = linea.split('"')[1].split('"')[0]

        # coeffs de EQ
        if coeffIniciado:
            if "c_eq" in linea:
                c_eqIniciado = True
        if c_eqIniciado:
            if "filename:" in linea:
                cFilename = linea.split('"')[1].split('"')[0].split("/")[-1]
                coeffs.append([coeffIndex, cName, cFilename])
                c_eqIniciado = False

        # coeffs de DRC
        if coeffIniciado:
            if "c_drc" in linea:
                c_drcIniciado = True
        if c_drcIniciado:
            if "filename:" in linea:
                cFilename = linea.split('"')[1].split('"')[0].split("/")[-1]
                coeffs.append([coeffIndex, cName, cFilename])
                c_drcIniciado = False

        # coeffs de filtrado LP
        if coeffIniciado:
            if "c_lp" in linea:
                c_lpIniciado = True
        if c_lpIniciado:
            if "filename:" in linea:
                cFilename = linea.split('"')[1].split('"')[0].split("/")[-1]
                coeffs.append([coeffIndex, cName, cFilename])
                c_lpIniciado = False

        # coeffs de filtrado MP
        if coeffIniciado:
            if "c_mp" in linea:
                c_mpIniciado = True
        if c_mpIniciado:
            if "filename:" in linea:
                cFilename = linea.split('"')[1].split('"')[0].split("/")[-1]
                coeffs.append([coeffIndex, cName, cFilename])
                c_mpIniciado = False

        # coeffs de filtrado DIRAC PULSE
        if coeffIniciado:
            if "c_dirac" in linea:
                c_diracIniciado = True
        if c_diracIniciado:
            if "filename:" in linea:
                cFilename = linea.split('"')[1].split('"')[0].split("/")[-1]
                coeffs.append([coeffIndex, cName, cFilename])
                c_diracIniciado = False


        # Recopilamos las etapas de FILTRADO
        if linea.startswith("filter "):
            filterIniciado = True
            filterIndex +=1
            fName = linea.split('"')[1].split('"')[0]

        # Filtrado de EQ
        if filterIniciado:
            if "f_eq" in linea and linea.startswith("filter "):
                f_eqIniciado = True
        if f_eqIniciado:
            if "coeff:" in linea:
                cName = linea.split(':')[1].strip().replace('"', '').replace(";","")
                filters_at_start.append([filterIndex, fName, cName])
                f_eqIniciado = False

        # Filtrado de DRC
        if filterIniciado:
            if "f_drc" in linea and linea.startswith("filter "):
                f_drcIniciado = True
        if f_drcIniciado:
            if "coeff:" in linea:
                cName = linea.split(':')[1].strip().replace('"', '').replace(";","")
                filters_at_start.append([filterIndex, fName, cName])
                f_drcIniciado = False

        # Filtrado de via FR
        if filterIniciado:
            if "f_fr" in linea and linea.startswith("filter "):
                f_frIniciado = True
        if f_frIniciado:
            if "coeff:" in linea:
                cName = linea.split(':')[1].strip().replace('"', '').replace(";","")
                filters_at_start.append([filterIndex, fName, cName])
                f_frIniciado = False

        # Filtrado de via LOW
        if filterIniciado:
            if "f_lo" in linea and linea.startswith("filter "):
                f_loIniciado = True
        if f_loIniciado:
            if "coeff:" in linea:
                cName = linea.split(':')[1].strip().replace('"', '').replace(";","")
                filters_at_start.append([filterIndex, fName, cName])
                f_loIniciado = False

        # Filtrado de via MID
        if filterIniciado:
            if "f_mi" in linea and linea.startswith("filter "):
                f_miIniciado = True
        if f_miIniciado:
            if "coeff:" in linea:
                cName = linea.split(':')[1].strip().replace('"', '').replace(";","")
                filters_at_start.append([filterIndex, fName, cName])
                f_miIniciado = False

        # Filtrado de via HI
        if filterIniciado:
            if "f_hi" in linea and linea.startswith("filter "):
                f_hiIniciado = True
        if f_hiIniciado:
            if "coeff:" in linea:
                cName = linea.split(':')[1].strip().replace('"', '').replace(";","")
                filters_at_start.append([filterIndex, fName, cName])
                f_hiIniciado = False

        # Filtrado de via SUBWOOFER
        if filterIniciado:
            if "f_sw" in linea and linea.startswith("filter "):
                f_swIniciado = True
        if f_swIniciado:
            if "coeff:" in linea:
                cName = linea.split(':')[1].strip().replace('"', '').replace(";","")
                filters_at_start.append([filterIndex, fName, cName])
                f_swIniciado = False

def lee_running_config():
    """ lee los filtros que hay corriendo en Brutefir
    """
    global filters_running
    filters_running = []
    
    # consultamos el comando 'lf' en Brutefir:
    printado = brutefir_cli.bfcli("lf; quit")
    
    for linea in printado.split("\n"):
        if ': "' in linea:
            f_name = linea.split('"')[-2]
        if "coeff set:" in linea:
            c_set = linea.split(":")[1].split()[0]
            filters_running.append([f_name, c_set])
    
    # tenemos los nombres de los filtros con el número de coeficiente cargado en cada filtro,
    # ahora añadiremos el nombre y el file_name del coeficiente.
    for f in filters_running:
        f_name, f_coeff = f                 # ej: ['f_fr_L', '10']
        for c in coeffs:
            c_num, c_name, c_filename = c   # ej: [10, 'c_lp-fr1', 'lp-fr_oct2_60Hz_1stOrd.pcm']
            if str(c_num) == f_coeff:
                f.append(c_name)
                f.append(c_filename)
        if f_coeff == "-1":
            f.append("(no filter)")
            f.append("")

def main():
    """ printa coeffs, filters_running, mapeo de salidas y salidas conectadas
    """

    lee_config()
    lee_running_config()
    
    print "\n--- Outputs map:"
    for x in outputs:
        print x

    print "\n--- Coeffs available:"
    tmp = [["coeff#:", "coeff_name:", "coeff_pcm_name:"]] + coeffs
    for x in tmp:
        print " "*14        + str(x[0]).rjust(2).ljust(8) + x[1].ljust(16) + x[2] 
    
    print "\n--- Filters Running:"
    tmp = [["filter_name:", "coeff#:", "coeff_name:", "coeff_pcm_name:"]] + filters_running
    for x in tmp:
        print x[0].ljust(14) + x[1].rjust(2).ljust(8) + x[2].ljust(16) + x[3]

    print "\n--- Jack:"
    for x in jc.jackConexiones("brutefir", "*"):
        print x[0].ljust(30) + x[1].ljust(8) + x[2]

    print
    
    # return coeffs, filters_running
   
if __name__ == "__main__" :

    main()
    
    
    

#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    Módulo para uso interno desde do_brutefir_config.py.
    
    Se confecciona una lista clasificada con todos los filtros pcm
    encontrados en la carpeta del altavoz solicitada,
    y se  escribe en el archivo /home/firtro/lspk/altavoz/Fs/filters.scan

    Nota: la lista muestra la ganacia de los filtros pcm
          si se acompañan de un archivo ini, para comodidad
          del usuario que construye la carpeta del altavoz.

"""
# v0.2
# - Se adecúa con ocasión de la vuelta a tener los PCM de DRC en la "audio_folder" lspk/ALTAVOZ/FS/
# - Se renombre filters.ini --> filters.scan que refleja mejor la naturaleza de este archivo.

import os, sys
import ConfigParser # usado para leer la ganancia del .INI asociado a los .PCM

HOME = os.path.expanduser("~")
sys.path.append(HOME + "/bin")
from getstatus import fs

avisos = ""

def buscaDRCs(carpeta): # filtros de DRC

    f1.write("\n[drcs]\n")

    # Lista de los pcm relativos a DRC
    # La ordenamos por la pos 7: 'drc-1-Lxxxxxxxxxxx"
    #                                    ^---(pos7)
    drcPCMs = sorted([x for x in os.listdir(carpeta) if x[:4]=="drc-" and x[-4:]==".pcm"],
                      key=lambda x: x[7:])

    drcPCMs = [carpeta+"/"+x for x in drcPCMs]

    filterVersions = []

    for drcPCM in drcPCMs:

        gain = lee_INI_of_PCM(drcPCM, 'gain')

        basename = drcPCM.split("/")[-1]
        indice = basename[4]
        canal = basename[6].upper()
        coeff_name = "c_drc" + indice + "_" + canal
 
        f1.write(coeff_name + " = " + gain.rjust(6) + "  " + drcPCM + "\n")

        filterFile = drcPCM.split("/")[-1]
        filterVersion = filterFile[1:].strip().replace(".pcm", "")
        if filterVersion not in filterVersions:
            filterVersions.append(filterVersion)

def buscaXOs(carpeta): # filtros de CORTE DE VIAS y/o FULL RANGE

    # Eludimos los .pcm que no estén 'bien nombrados'
    prefis = ['lp-', 'mp-']
    vias   = ['-fr', '-lo', '-mi', '-hi']
    xoFiles = [ x for x in os.listdir(carpeta) if x[:3] in prefis and x[2:5] in vias and x.endswith(".pcm")]
    # Le añadimos el path absoluto
    xoFiles = [ carpeta + "/" + x for x in xoFiles ]

    for phase in ('lp', 'mp'):

        f1.write("\n[" + phase + "_xo]\n") # separador de sección del ini

        # Colección de PCMs de la phase que toque lp|mp
        xoFilesPhase = [ x for x in xoFiles if x.split("/")[-1].startswith(phase + '-')]
        xoFilesPhase.sort()

        i = 0
        last_via = ''
        for xoFile in xoFilesPhase:

            gain = lee_INI_of_PCM(xoFile, 'gain')
            via = xoFile.split("/")[-1][3:5]
            if last_via <> via:
                i = 0
            last_via = via
            
            f1.write("c_" + phase + "-" + xoFile.split("-")[1][:2]
                     + "_" + str(i) + " = " + gain.rjust(6) + "  " + xoFile + "\n")
            i +=1

def buscaSWs(carpeta): # filtros de SUBWOOFERS

    # Eludimos los .pcm que no estén 'bien nombrados'
    prefis = ['lp-', 'mp-']
    vias   = ['-sw']
    swFiles = [ x for x in os.listdir(carpeta) if x[:3] in prefis and x[2:5] in vias and x.endswith(".pcm")]
    # le añadimos el path absoluto
    swFiles = [ carpeta + "/" + x for x in swFiles ]

    for phase in ('lp', 'mp'):

        f1.write("\n[" + phase + "_sw]\n")

        # set of files of refered phase
        swFilesPhase = [ x for x in swFiles if x.split("/")[-1].startswith(phase + '-')]
        swFilesPhase.sort()

        i = 0
        for swFile in swFilesPhase:

            gain = lee_INI_of_PCM(swFile, 'gain')

            f1.write("c_" + phase + "-" + swFile.split("-")[1][:2]
                     + "_" + str(i) + " = " + gain.rjust(6) + "  " + swFile + "\n")
            i += 1

def lee_INI_of_PCM(pcmFile, option):
    ''' cada .pcm tiene asociado un .INI a modo de metadatos,
        en principio tiene la ganancia del filtro
    '''
    global avisos

    ini_of_pcm = ConfigParser.ConfigParser()

    # intentamos leer el "INI" asociado
    if ini_of_pcm.read(pcmFile.replace(".pcm", ".ini")):
        for section in ini_of_pcm.sections():
            if "gain" in ini_of_pcm.options(section):
                return ini_of_pcm.get(section, "gain")

    # si el intento de lectuta del INI es una lista vacía:
    else:
        return '-00.00'
        avisos +=  "(!) no se localiza información de ganancia de " + pcmFile + "\n"

def main(carpeta):

    global f1, avisos

    f1 = open(carpeta + "/filters.scan", "w")
    f1.write("; (i) NO editar.\n")
    f1.write("; Este archivo es el resultado de escanear los archivos .PCM de filtrado\n")
    f1.write("; y sus archvos .INI asociados que contienen la ganacia de cada filtro .PCM\n")

    buscaDRCs(carpeta)
    buscaXOs(carpeta)
    buscaSWs(carpeta)

    f1.close()

    return avisos

if __name__ == '__main__':
    print __doc__

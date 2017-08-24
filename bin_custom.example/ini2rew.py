#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    toma un archivo .peq de filtros paramétricos del FIRtro
    y añade el valor de Q en función del BW en cada filtro.
    El objetivo es poder transcribir los un set de filtros que
    hayamos modificado a REW.

    uso:
        ini2rew.py archivo.peq
"""

import math
import sys

def bw2q(BW):
    """
    'http://www.bmltech.com/refbook/audio'
    """
    return math.sqrt(2**BW) / (2**BW -1)

def peqFile2list(fname):
    f = open(fname, 'r')
    conte = f.read().split("\n")
    f.close()

    filters = []
    canal = ''

    for linea in conte:

        # flag de cada sección izquierda o derecha
        if "[left]" in linea:
            canal = 'L'
        if "[right]" in linea:
            canal = 'R'

        # tomamos nota de los parámetros del filtro
        if canal:
            if linea and linea[0] == "f":
                onoff, fc, bw, gain = linea.split()[2:6]
                q = str(bw2q(float(bw)))
                if onoff == "1":
                    filters.append([canal, fc, bw, gain, q])

    # devuelve la lista ordenada primero por canal y luego por frecuencia central
    return sorted(filters, key = lambda filters: (filters[0], filters[1]))

def fmt1(x):
    # 6 digitos significativos con 1 decimal
    return "{:5.1f}".format(float(x))

def fmt4(x):
    # 6 digitos significativos con 4 decimales
    return "{:5.4f}".format(float(x))

def printa(filtros):
    print "ch    Fc   (BW)      Gain    Q"
    last_ch = ""
    for f in filtros:
        curr_ch = f[0]
        if curr_ch <> last_ch:
            print
        last_ch = curr_ch
        print curr_ch.ljust(5) + fmt1(f[1]) + " (" + fmt4(f[2]) + ") " + fmt1(f[3]) + "  " +  fmt1(f[4])


if __name__ == '__main__':

    print
    filtros = peqFile2list(sys.argv[1])
    printa(filtros)
    print

#    except:
#        print __doc__


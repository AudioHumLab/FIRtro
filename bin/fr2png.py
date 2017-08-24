#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" 
    Módulo para hacer la gráfica de una FR en texto plano .frd, .txt
    v0.1: lee archivos proporcionados por RoomEqWizard
    
    Uso desde la línea de comandos:
    fr2png.py "/path/to/xxxx.txt" [-p para mostrar la gráfica]
    
    Se genera un archivo .PNG en la misma carpeta de archivo de texto.
"""
import peq2fr
import numpy as np
import matplotlib.pyplot as plt
from sys import argv as sys_argv, path as sys_path

# esto es para los modulos del FIRtro
from os import path as os_path
HOME = os_path.expanduser("~")
sys_path.append(HOME + "/bin")
from basepaths import loudspeaker_folder
from getconfig import loudspeaker
altavoz_folder = loudspeaker_folder + loudspeaker

def plotFR(FR, pngname):
    """ plotea una Frequency Response de un número arbitrario de puntos
    """
    plt.close()
    plt.figure(figsize=(16/2, 9/2))
    plt.title('Frequency Response')
    plt.xlim((20, 20000))
    plt.xscale("log")
    plt.grid()
    
    frecs, gaindB = FR
    plt.plot(np.abs(frecs), np.abs(gaindB), linestyle="-", linewidth=2.0)

    plt.savefig(pngname)
    if plotea:
        plt.show()

def leeFrREW(txtfile):
    """ Lee un archivo .txt de respuesta de frecencias de RoomEqWizard.
        - frecuencias en la primera columna 
        - amplitud  en la segunda columna
        - fase en la tercera columna
        
        Devuelve la matriz traspuesta del archivo, es decir 
        una numpy array de 3 x Npuntos (frecuencias, amplitudes y grados)
    """
    return np.loadtxt(txtfile, comments="*", unpack=True)

def REWtxt2png(txtfile):
    """ Funcion principal para variantes de archivos de respuesta en
        frecuencia de RoomEQWizard
    """
    txtdata = leeFrREW(txtfile)

    FR = np.zeros(shape=(2,59382), dtype=complex)
    freq, mag, deg = txtdata
    FR[0] = freq
    for n in range(len(FR[1])):
        FR[1][n] =  np.complex(mag[n]*np.cos(deg[n]*np.pi/180.0), 
                               mag[n]*np.sin(deg[n]*np.pi/180.0))

    pngname = txtfile.replace(".txt", ".png")
    plotFR(FR, pngname)  

if __name__ == "__main__":
    
    plotea = False
    try:
        txtname = sys_argv[1]
        try:
            if sys_argv[2] == "-p":
                plotea = True
        except:
            pass    
        REWtxt2png(txtname)
 
    except:
        print __doc__





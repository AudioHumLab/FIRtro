#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" peq2fr.py script para transformar un EQ paramétrico
    en un array de FR (frecuency response)
    Como paso intermedio se hace una transformacion 
    de PEQ (F0, BW, Gain) a Biquads ((b0, b1, b2), (a0, a1, a2))
"""

import numpy as np
from scipy import signal
import ConfigParser

def leePEQ_canal(peqfile, canal):
    """ Lee un canal de un fichero XXX.peq de parametricos del FIRtro
        y devuelve las tripletas de los EQs ACTIVOS del canal (Frec, BW, Gain)
    """
    # leemos el archivo de EQs XXXX.peq (es una estructura INI)
    PEQs = ConfigParser.ConfigParser()
    PEQs.read(peqfile)
    # lista de almacenamiento de tripletas de EQs paramétricos
    peqs = []
    # leemos los PEQ del canal indicado:
    for option in PEQs.options(canal):
        # descartamos los ajustes de ganacia global de cada plugin
        if not "global" in option:
            # f1       = 1      47.4    0.0818    -6.2 , etc...
            peq = PEQs.get(canal, option).split()
            # lo añadimos a la lista si está activado.
            if peq[0] == "1":
                peqs.append( [ float(peq[1]), float(peq[2]), float(peq[3]) ] )

    # Ejemplo:
    #    peqs =  [
    #            ( 47.4  ,  0.0818  ,  -6.2 ),
    #            ( 50.6  ,  0.1884  ,   4.0 ),
    #            ( 56.2  ,  0.1033  ,  -9.9 ),
    #            (  100  ,  0.1318  ,  -4.6 ),
    #            (  144  ,  0.1294  ,  -6.6 ),
    #            (  173  ,  0.0722  ,  -4.7 ),
    #            (  215  ,  0.2880  ,  -3.5 ),
    #            (  263  ,  0.2880  ,  -1.7 ),
    #            (  301  ,  0.2897  ,   3.1 ),
    #            (  534  ,  0.4771  ,  -4.0 ),
    #            ]

    return peqs

def _q2bw(Q):
    """ convierte Q a BW
        http://www.rane.com/note167.html#qformula
        http://www.rane.com/note170.html
    """
    bw = 2.0 / np.log10(2.0) * np.log10( 0.5 * (1/Q + np.sqrt(1/Q**2 + 4)))
    return bw

def biquad2peq(Fs, b, a):
    """ OjO REVISAR ESTO NO FUNCIONA 
        https://www.dsprelated.com/showthread/comp.dsp/36946-1.php
    """
    b0, b1, b1 = b
    a0, a1, a2 = a
    w0 = np.arccos(-b1 / 2)
    f0 = w0 * Fs / ( 2 * np.pi)

    A = np.sqrt( (b0-1) / (1-a2) )
    dBgain = np.log10(A) * 40

    alpha = np.sqrt( (1-a2) * (b0-1) )
    Q = np.sin(w0) / (2 * alpha)
    
    BW = _q2bw(Q)
    
    print "OjO REVISAR ESTO NO FUNCIONA"
  
    return (Fs, f0, BW, dBgain)

def peqBW_2_biquad(Fs=44100, f0=1000, BW=1, dBgain=-3.0):
    """ http://www.musicdsp.org/files/Audio-EQ-Cookbook.txt
        convierte parámetros EQ (f0, BW, gain) a biquads
    """
    A = 10**(dBgain / 40.0)
    w0 = 2.0 * np.pi * f0 / Fs
    alpha = np.sin(w0) * np.sinh( np.log(2) / 2 * BW * w0 / np.sin(w0) )
    
    # peakingEQ:
    b0 =   1.0 + alpha * A
    b1 =  -2.0 * np.cos(w0)
    b2 =   1.0 - alpha * A
    a0 =   1.0 + alpha / A
    a1 =  -2.0 * np.cos(w0)
    a2 =   1.0 - alpha / A
    return (b0, b1, b2), (a0, a1, a2)

def peqQ_2_biquad(Fs=44100, f0=1000, Q=2, dBgain=-3.0):
    """ http://www.musicdsp.org/files/Audio-EQ-Cookbook.txt
        convierte parámetros EQ (f0, Q, gain) a biquads
    """
    A = 10**(dBgain / 40.0)
    w0 = 2.0 * np.pi * f0 / Fs
    alpha = np.sin(w0) / (2 * Q)
    
    # peakingEQ:
    b0 =   1.0 + alpha * A
    b1 =  -2.0 * np.cos(w0)
    b2 =   1.0 - alpha * A
    a0 =   1.0 + alpha / A
    a1 =  -2.0 * np.cos(w0)
    a2 =   1.0 - alpha / A
    return (b0, b1, b2), (a0, a1, a2)

def peqBW_2_fr(Fs, peqs):
    """ convierte EQs paramétricos en FRs (frequency responses array) 
        parameters: peqs = array tripletas de EQs paramétricos)
        returns: FRs = array de FR (w,h)
    """
    FRs = []
    for f0, BW, dBgain in peqs:
        b, a = peqBW_2_biquad(Fs, f0, BW, dBgain)
        w, h = signal.freqz(b, a, worN=int(Fs))
        FRs.append([w,h])
    return FRs
    
def frSum(Fs, frs):
    """ suma las ganancias de varias FR (respuestas de frecuencia)
        nota: se asume que las frecuencias son homogeneas en cada FR
    """
    hsum = np.zeros(Fs)
    hsum = hsum + (1 + 0j)
    for w, h in frs:        
        hsum *= h
    return [w, hsum]

if __name__ == "__main__":
    pass


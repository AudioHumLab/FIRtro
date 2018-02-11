#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    v0.1 BETA
    Visor de archivos de respuesta en frecuencia .FRD
    
    Uso:
    frd_viewer.py [flow-fhigh] path/to/file1.frd [path/to/file2.frd ...]
    
    See also:  fir_viewer.py
    
"""

import sys
import numpy as np
from scipy import signal, interpolate
from scipy.stats import mode
from matplotlib import pyplot as plt
from matplotlib import gridspec
from matplotlib import ticker

def readFRD(fname):
    f = open(fname, 'r')
    lineas = f.read().split("\n")
    f.close()
    fr = []
    for linea in [x[:-1].replace("\t", " ").strip() for x in lineas if x]:
        if linea[0].isdigit():
            linea = linea.split()
            f = []
            for col in range(len(linea)):
                dato = float(linea[col])
                if col == 2: # hay columna de phases en deg
                    dato = round(dato / 180.0 * np.pi, 4)
                f.append(dato)
            fr.append(f)
    return np.array(fr)

def prepara_eje_frecuencias(ax):
    freq_ticks=[20, 100, 1000, 10000, 20000]
    ax.grid(True)
    ax.set_xscale("log")
    fmin2 = 20; fmax2 = 20000
    if fmin:
        fmin2 = fmin
    if fmax:
        fmax2 = fmax
    ax.set_xticks(freq_ticks)
    ax.get_xaxis().set_major_formatter(ticker.ScalarFormatter())
    ax.set_xlim([fmin2, fmax2])

def prepara_graf():
    fig = plt.figure()
    grid = gridspec.GridSpec(nrows=2, ncols=1)    

    axMag = fig.add_subplot(grid[0,0])
    axMag.set_ylim(-40,5)
    prepara_eje_frecuencias(axMag)
    axMag.set_ylabel("magnitude (dB)")
    
    axPha = fig.add_subplot(grid[1,0])
    prepara_eje_frecuencias(axPha)
    axPha.set_ylim([-180.0,180.0])
    axPha.set_yticks(range(-135, 180, 45))
    axPha.grid(linestyle=":")
    axPha.set_ylabel("phase / --- min phase (deg)")
    
    return axMag, axPha

def lee_command_line():
    global frdnames, fmin, fmax, autolevel
    
    frdnames = []
    autolevel = False

    if len(sys.argv) == 1:
        print __doc__
        sys.exit()
    else:
        for opc in sys.argv[1:]:

            if opc in ("-h", "-help", "--help"):
                print __doc__
                sys.exit()

            elif "-" in opc and opc[0].isdigit() and opc[-1].isdigit:
                fmin, fmax = opc.split("-")
                fmin = float(fmin)
                fmax = float(fmax)

            elif opc == '-autolevel':
                autolevel = True

            else:
                frdnames.append(opc)

    # si no hay pcms o si no hay (Fs xor ini)
    if not frdnames:
        print __doc__
        sys.exit()

def BPavg(curve):
    """ cutre estimación del promedio de una curva de magnitudes dB en la banda de paso 
    """
    # Suponemos que la curva es de tipo band-pass maomeno plana
    # Elegimos los bins que están a poca distancia del máximo de la curva
    bandpass_locations = np.where( curve > max(curve) - 12)
    bandpass = np.take( curve, bandpass_locations)
    # Buscamos los valores más frecuentes de la zona plana 'bandpass' redondeada a .1 dB
    avg = mode(np.round(bandpass,1), axis=None)[0][0]
    return avg

def limpia(pha, mag, th):
    #--- Extraemos la wrapped PHASE de la FR 'h'
    # Eliminamos (np.nan) los valores de phase fuera de la banda de paso,
    # por ejemplo de magnitud por debajo de -80 dB
    phaClean  = np.full((len(pha)), np.nan)
    mask = (mag > th)
    np.copyto(phaClean, pha, where=mask)
    return phaClean

if __name__ == "__main__":

    # Por defecto
    fmin = 20; fmax = 20000

    # Lee archivos .frd y limites de frecuencias 
    lee_command_line()
    
    # Prepara graficas
    axMag, axPha = prepara_graf()
    
    # Usaremos un nuevo eje de frecuencias comun sobre el que interpolaremos
    # las FRDs de los archivos leidos que pueden diferir
    freq = np.logspace(np.log10(fmin), np.log10(fmax), num=500)

    for frdname in frdnames:
        drivername = frdname.split("/")[-1].split(".")[:-1][0]
        frd =  readFRD(frdname)
        # Vemos si hay columna de phase
        hay_fase = (frd.shape[1] == 3)

        # arrays de freq, mag y pha
        freq0 = frd[::, 0]
        mag0  = frd[::, 1]

        # Funcion de interpolacion con los datos leidos
        fmag = interpolate.interp1d(freq0, mag0, kind="linear", bounds_error=False)
        # Interpolación sobre nuestro eje 'freq'
        mag = fmag(freq)
        # La bajamos por debajo de 0
        mag -= np.max(mag)
        if autolevel:
            mag -= BPavg(mag)
            axMag.set_title("auto levels")
    
        # Fase mínima ??
        H = signal.hilbert(mag)
        mpha = np.angle(H, deg=True)
        
        # Plot 
        axMag.plot(freq, mag, label=drivername)
        color = axMag.lines[-1].get_color() # anotamos el color

        axPha.plot(freq, mpha, "--", linewidth=1.0, color=color)        

        if hay_fase:
        
            pha0  = frd[::, 2]
            fpha = interpolate.interp1d(freq0, pha0, kind="linear", bounds_error=False)
            pha = fpha(freq)
            pha = pha * 180.0 / np.pi
            #pha = limpia(pha=pha, mag=mag, th=-50.0)
            
            # Plot
            axPha.plot(freq, pha, "-", linewidth=1.0, color=color)
    
    axMag.legend(loc='lower right', prop={'size':'small', 'family':'monospace'})
    axPha.legend(loc='lower left', prop={'size':'small', 'family':'monospace'})
    plt.show()




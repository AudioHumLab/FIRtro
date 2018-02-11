#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    v0.4 BETA
    
    Visor de archivos FIR xover y de archivos FRD (freq. response).
    Se muestra la magnitud y fase de los FIR.

    Este visor está orientado al proyecto FIRtro
        https://github.com/AudioHumLab/FIRtro

    Cada 'viaX.pcm' puede tener asociado un archivo 'viaX.ini'
    que especifica la Fs y la ganacia aplicada en el convolver.

    Además, si se proporcionan archivos 'viaX.frd' con la FRD del altavoz usado 
    en cada via, se visualizará el resultado estimado al aplicar los filtros.

    También se pueden visualizar archivos FIR .pcm o .bin sueltos,
    indicando la Fs en la linea de comandos.

    Acepta archivos FIR en formato PCM float32. Los archivos FRD de la respuesta
    del altavoz pueden tener hasta tres columnas (frecuencia, magnitud  y fase).

    Archivo de configuración del ploteo: fir_viewer.cfg

    Uso:
    
    fir_viewer.py [ini|xxx] path/to/filtro1.pcm  [path/to/filtro2.pcm ... ] [flow-fhigh]

          ini:        Lee Fs y Gain en los archivos '.ini' asociados a '.pcm'
          xxx:        Toma xxxx como Fs y se ignoran los '.ini'
          flow-fhigh: Rango de frecuencias de la gráfica (opcional, util para un solo fir)

    Ejemplo de archivo 'viaX.ini':

        [miscel]
        fs      = 441000
        gain    = -6.8     # Ganancia ajustada en el convolver.
        gainext = 8.0      # Resto de ganancia incluyendo la potencia final
                             radiada en el eje de escucha.
                             
    See also: frd_viewer.py
    
"""
#
# v0.1:
#   Límites de ploteo en .cfg
#   Lee 'filterN.ini' asociado a 'filterN.pcm'
#   Fs opcional en command line
# v0.2:
#   Uso de scipy.signal.freqz
#   Gráficas de magnitud y phase de los fltros xover '.pcm'
# v0.3:
#   Descartar el ploteo de la phase fuera de la banda de paso de los filtros.
# v0.4:
#   Si están disponibles las FRDs de los altavoces se muestra el resultado del filtrado.
#   Detecta clips en los FIR de xover
#   Rango de frecuencias en linea de comandos opcional, útil para representar una sola vía.

import sys
import os.path
import numpy as np
from scipy import signal, interpolate
from scipy.stats import mode    # Usada en la función BPavg
from matplotlib import pyplot as plt
from matplotlib import ticker   # Para rotular a medida
from matplotlib import gridspec # Para ajustar disposición de los subplots
from ConfigParser import ConfigParser

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

def readConfig():
    """ lee la gonfiguracion del ploteo desde fir_viewer.cfg"""
    config = ConfigParser()
    cfgfile = os.path.dirname(os.path.realpath(__file__)).replace("\\", "/") + "/fir_viewer.cfg"
    config.read(cfgfile)
    global DFTresol
    global frec_ticks, fig_size
    global top_dBs, range_dBs, fmin, fmax

    top_dBs         = config.getfloat   ("plot", "top_dBs")
    range_dBs       = config.getfloat   ("plot", "range_dBs")
    fmin            = config.getfloat   ("plot", "fmin")
    fmax            = config.getfloat   ("plot", "fmax")
    fig_width       = config.getfloat   ("plot", "fig_width")
    fig_height      = config.getfloat   ("plot", "fig_height")
    tmp             = config.get        ("plot", "frec_ticks").split()
    frec_ticks      = [int(x) for x in tmp]
    fig_size        = (fig_width, fig_height)

def readPCM32(fname):
    """ lee un archivo pcm float32
    """
    #return np.fromfile(fname, dtype='float32')
    return np.memmap(fname, dtype='float32', mode='r')

def readPCMini(f):
    """ lee el .ini asociado a un filtro .pcm de FIRtro
    """
    iniPcm = ConfigParser()
    fs = 0
    gain = 0.0
    gainext = 0.0
    if os.path.isfile(f):
        iniPcm.read(f)
        fs      = float(iniPcm.get("miscel", "fs"))
        gain    = float(iniPcm.get("miscel", "gain"))
        gainext = float(iniPcm.get("miscel", "gainext"))
    else:
        print "(!) no se puede accecer a " + f
        sys.exit()
    return fs, gain, gainext

def prepara_eje_frecuencias(ax):
    """ según las opciones fmin, fmax, frec_ticks de fir_viewer.cgf """
    ax.set_xscale("log")
    fmin2 = 20; fmax2 = 20000
    if fmin:
        fmin2 = fmin
    if fmax:
        fmax2 = fmax
    ax.set_xticks(frec_ticks)
    ax.get_xaxis().set_major_formatter(ticker.ScalarFormatter())
    ax.set_xlim([fmin2, fmax2])

def lee_command_line():
    global fs_commandline, lee_inis, pcmnames, fmin, fmax
    fs_commandline = ""
    lee_inis = False
    pcmnames = []

    if len(sys.argv) == 1:
        print __doc__
        sys.exit()
    else:
        for opc in sys.argv[1:]:
            if opc in ("-h", "-help", "--help"):
                print __doc__
                sys.exit()
            elif opc.isdigit():
                fs_commandline = float(opc)
            elif opc == "ini":
                lee_inis = True
            elif "-" in opc and opc[0].isdigit() and opc[-1].isdigit():
                fmin, fmax = opc.split("-")
                fmin = float(fmin)
                fmax = float(fmax)
            else:
                pcmnames.append(opc)

    # si no hay pcms o si no hay (Fs xor ini)
    if not pcmnames or not (bool(fs_commandline) ^ lee_inis):  # '^' = 'xor'
        print __doc__
        sys.exit()

def lee_params(pcmname):
    """ Lee ganancias y Fs indicadas el el .ini asociado al filtro .pcm """
    gain    = 0.0
    gainext = 0.0
    if fs_commandline:      # no se lee el .ini
        fs = fs_commandline
    else:                   # se lee el .ini
        fini = "".join(pcmname.split(".")[:-1]) + ".ini"
        fs, gain, gainext = readPCMini(fini)
    return fs, gain, gainext

def estima_N(taps):
    # NOTA BETA: 
    # Hacemos la DFT con un nº de bins potencia de 2 PERO sin incurrir en ¿aliasings?
    # Experimentalmente no hay que superar taps/4, si no sale chungo.
    n = 9 # 2^9 = 512 bins para empezar
    while True:
        N = 2 ** n
        res = fs / N
        if N >= taps / 4:
            N = 2 ** (n-1)
            #print "taps:", len(imp), "dftN:", N , "dftRes:", str(round(fs/N, 2))
            break
        n += 1
    return N

def frd_of_pcm(f):
    """ devuelve el nombre del .frd asociado al filtro .pcm (o .bin)
    """
    f = f.replace("\\", "/")
    if "/" in f:
        path = "/".join(f.split("/")[:-1]) + "/"
        f = f.split("/")[-1]
    else:
        path = "./" 
    return path + f[3:].replace(".pcm", ".frd").replace(".bin", ".frd")

def KHz(f):
    """ cutre formateo de frecuencias en Hz o KHz """
    f = int(round(f, 0))
    if f in range(1000):
        f = str(f) + "Hz"
    else:
        f = round(f/1000.0, 1)
        f = str(f) + "KHz"
    return f.ljust(8)
    
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

def hroomInfo(magdB, via):
    gmax = np.amax(magdB)
    fgmax = freqs[np.argmax(magdB)]
    tmp1 = str(round(gmax, 1)).rjust(5) + "dBFS"   # dBs maquillados
    tmp2 = KHz(fgmax)                              # frec en Hz o KHz
    info = via[:12].ljust(12) + " max:" + tmp1 + "@ " + tmp2
    # Tenemos en cuenta la gain del .INI si se hubiera facilitado
    if gmax + gain > 0:
        print "(!) Warning CLIP: " + info
    return info

def prepararaGraficas():
    global fig, grid, axMag, axDrv, axPha, axGD, axIR
    #-------------------------------------------------------------------------------
    # Preparamos el área de las gráficas 'fig'
    #-------------------------------------------------------------------------------
    fig = plt.figure(figsize=fig_size)
    # Para que no se solapen los rótulos
    fig.set_tight_layout(True)

    # Preparamos una matriz de Axes (gráficas).
    # Usamos GridSpec que permite construir un array chachi.
    # Las gráficas de MAG ocupan 3 filas, la de PHA ocupa 2 filas,
    # y la de IR será de altura simple, por tanto declaramos 6 filas.
    grid = gridspec.GridSpec(nrows=6, ncols=len(pcmnames))

    # --- SUBPLOT para pintar las FRs (alto 3 filas, ancho todas las columnas)
    axMag = fig.add_subplot(grid[0:3, :])
    axMag.grid(linestyle=":")
    axMag.set_ylim([top_dBs - range_dBs, top_dBs])
    axMag.set_ylabel("filter magnitude dB")
    
    # --- SUBPLOT compartido para pintar los .FRD de los altavoces
    axDrv = axMag.twinx()
    axDrv.grid(linestyle=":")
    axDrv.set_ylabel("--- driver magnitude dB")
    # Lo reubicamos 10 dB abajo para claridad de lectura 
    axDrv.set_ylim([top_dBs - range_dBs + 10, top_dBs + 10])
    prepara_eje_frecuencias(axDrv)

    # --- SUBPLOT para pintar las PHASEs (alto 2 filas, ancho todas las columnas)
    axPha = fig.add_subplot(grid[3:5, :])
    axPha.grid(linestyle=":")
    prepara_eje_frecuencias(axPha)
    axPha.set_ylim([-180.0,180.0])
    axPha.set_yticks(range(-135, 180, 45))
    axPha.set_ylabel(u"filter phase")
    #axPha.set_title("filter phase and GD:")

    # --- SUBPLOT para pintar el GD (común con el de las phases)
    # comparte el eje X (twinx) con el de la phase
    # https://matplotlib.org/gallery/api/two_scales.html
    axGD = axPha.twinx()
    axGD.grid(False)
    prepara_eje_frecuencias(axGD)
    axGD.set_ylim(0, 1000)
    axGD.set_ylabel(u"--- filter GD (ms)")

if __name__ == "__main__":

    # Lee la configuración de ploteo
    readConfig()        

    # Lee opciones command line: fs_commandline, lee_inis, pcmnames, fmin, fmax
    lee_command_line()

    # Prepara la parrilla de gráficas
    prepararaGraficas()

    # Aquí guardaremos las curvas de cada via
    vias = []

    hay_FRDs = False
    
    for pcmname in pcmnames:
    
        #--- Nombre de la vía
        tmp = pcmname.replace("\\", "/")
        via = tmp.split("/")[-1].replace(".pcm", "").replace(".bin", "")

        #--- Leemos el impulso IR y sus parámetros (Fs, gain)
        IR = readPCM32(pcmname)
        fs, gain, gainext = lee_params(pcmname)
        fNyq = fs / 2.0

        #---Obtenemos la FR 'h' en N bins:
        N = estima_N(taps=len(IR)) 
        #   usamos whole=False para computar hasta pi (Nyquist)
        #   devuelve: h - la FR  y w - las frec normalizadas hasta Nyquist
        w, h = signal.freqz(IR, worN=N, whole=False)
        # convertimos las frecuencias normalizadas en reales según la Fs
        freqs = (w / np.pi) * fNyq

        #--- Extraemos la MAG de la FR 'h'
        #    tomamos en cuenta la 'gain' del .ini que se aplicará como coeff del convolver
        firMagdB = 20 * np.log10(abs(h)) + gain

        #--- Extraemos la wrapped PHASE de la FR 'h'
        firPhase = np.angle(h, deg=True)
        # Eliminamos (np.nan) los valores de phase fuera de la banda de paso,
        # por ejemplo de magnitud por debajo de -80 dB
        firPhaseClean  = np.full((len(firPhase)), np.nan)
        mask = (firMagdB > -80.0)
        np.copyto(firPhaseClean, firPhase, where=mask)

        #--- Obtenemos el GD 'gd' en N bins:
        wgd, gd = signal.group_delay((IR, 1), N, whole=False)
        # convertimos las frecuencias normalizadas en reales según la Fs
        freqsgd = (wgd / np.pi) * fNyq
        # GD es en radianes los convertimos a en milisegundos
        firGDms = gd / fs * 1000
        # Limpiamos con la misma mask de valores fuera de la banda de paso usada arriba
        firGDmsClean  = np.full((len(firGDms)), np.nan)
        np.copyto(firGDmsClean, firGDms, where=mask)

        #--- Info del headroom dBFs en la convolución de este filtro pcm
        ihroom = hroomInfo(magdB = firMagdB, via=via)

        curva = {'via':via, 'IR':IR, 'mag':firMagdB, 'pha':firPhaseClean,
                           'gd':firGDmsClean, 'hroomInfo':ihroom}

        #--- Curvas de los .FRD de los altavoces (si existieran)
        frdname = frd_of_pcm(pcmname)
        if os.path.isfile(frdname):
            hay_FRDs = True
            frd = readFRD(frdname)
            frdFreqs = frd[::, 0]
            frdMag = frd[::, 1]
            
            # Como las frecuencias del FRD no van a coincidir con las 'freqs' de nuestra FFT,
            # hay que interpolar. Usamos los valores del FRD para definir la función de 
            # interpolación. Y eludimos errores si se pidieran valores fuera de rango.
            I = interpolate.interp1d(frdFreqs, frdMag, kind="linear", bounds_error=False, 
                                     fill_value="extrapolate")
            # Obtenemos las magnitudes interpoladas en nuestras 'freqs':
            frdMagIpol = I(freqs)
            # Y la reubicamos maomeno en 0 dBs
            frdMagIpol -= BPavg(frdMagIpol)
                        
            # Curva FR resultado de aplicar el filtro PCM a la FR del altavoz
            resMag = firMagdB + frdMagIpol
            # La reubicamos en 0 dB maomeno
            resMag -= BPavg(resMag)

            # Añadimos la curva del driver y el resultado del filtrado
            curva['driver']    = frdMagIpol
            curva['resultado'] = resMag

        else:
            print "(i) No se localiza la FR del driver: '" + frdname + "'"

        vias.append( curva )

    if hay_FRDs:
        #----------------------------------------------------------------
        # Curva mezcla de los resultados de filtrado de todas las vias:
        #----------------------------------------------------------------
        # Inicializamos una curva a -1000 dB ;-)
        mezclaTot = np.zeros(len(freqs)) - 1000
        # Y le vamos sumando las curvas resultado de cada via:
        for via in vias:
            resultado = via['resultado']
            mezclaTot = 20.0 * np.log10(10**(resultado/20.0) + 10**(mezclaTot/20.0))
        # La reubicamos en 0 dB
        mezclaTot -= BPavg(mezclaTot)
    
    #----------------------------------------------------------------
    # PLOTEOS
    #----------------------------------------------------------------
    columnaIR = 0

    for curva in vias:

        imp         = curva['IR']
        magdB       = curva['mag']
        phase       = curva['pha']
        gd          = curva['gd']
        info        = curva['hroomInfo']

        peakOffset = np.round(abs(imp).argmax() / fs, 3) # en segundos

        #--- MAG
        axMag.plot(freqs, magdB, "-", linewidth=1.0, label=info)
        color = axMag.lines[-1].get_color() # anotamos el color de la última línea

        #--- PHA
        axPha.plot(freqs, phase, "-", linewidth=1.0, color=color)

        #--- GD
        axGD.plot(freqs, gd, "--", linewidth=1.0, color=color)

        #--- IR. Nota: separamos los impulsos en columnas
        axIR = fig.add_subplot(grid[5, columnaIR])
        axIR.set_title("\npk offset " + str(peakOffset) + " s")
        axIR.set_xticks(range(0,len(imp),10000))
        axIR.ticklabel_format(style="sci", axis="x", scilimits=(0,0))
        axIR.plot(imp, "-", linewidth=1.0, color=color)
        columnaIR += 1

        if curva.has_key('driver'):
            driver      = curva['driver']
            resultado   = curva['resultado']
            #--- FR del driver
            axDrv.plot(freqs, driver, "--", linewidth=1.0, color=color)
            #--- FR resultado del filtrado
            axMag.plot(freqs, resultado, color="grey", linewidth=1.0)

    if hay_FRDs:
        axMag.plot(freqs, mezclaTot, color="black", linewidth=1.0, label="estimated")

    # Finalmente mostramos las gráficas por pantalla.
    # La leyenda mostrará las label indicadas en el ploteo de cada curva en 'axMag'
    axMag.legend(loc='lower left', prop={'size':'small', 'family':'monospace'})
    plt.show()

    #----------------------------------------------------------------
    # Y guardamos la gráficas en un PDF:
    #----------------------------------------------------------------
    print "\nGuardando en el archivo 'filters.pdf'"
    # evitamos los warnings del pdf 
    # C:\Python27\lib\site-packages\matplotlib\figure.py:1742: UserWarning: 
    # This figure includes Axes that are not compatible with tight_layout, so 
    # its results might be incorrect.
    import warnings
    warnings.filterwarnings("ignore")
    fig.savefig("filters.pdf", bbox_inches='tight')

    print "Bye!\n"

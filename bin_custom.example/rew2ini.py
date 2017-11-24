#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
 Convierte archivos .txt de filtros paramétricos de RoomEqWizard
 a una estructura '.ini' utilizable por el módulo Ecasound del FIRtro
 
 Uso:
 
 rew2ini.py  /path/to/left.txt /path/to/right.txt [ > fichero_de_salida ]

"""

import math
import sys

def q2bw(Q):
    """ http://www.rane.com/note167.html#qformula
        http://www.rane.com/note170.html
    """
    bw = 2.0 / math.log10(2.0) * math.log10( 0.5 * (1/Q + math.sqrt(1/Q**2 + 4)))
    return bw

def leeREW(fname):
    """ Devuelve el contenido de un archivo de texto 
        de filtros de REW.
    """
    f = open(fname, 'r')
    tmp = f.read()
    f.close()
    return tmp

def tabulaREW(printado):
    """ Lee un printado de texto de filtros de REW y se fija solo
        en las líneas de filtros paramétricos.
        Traduce el Q de REW a BW(oct)
        Devuelve una lista de quintupletas [Active, Fc, Gain, Q, BW]
    """
    lista = []
    for linea in printado.split("\n"):
        if "Filter" in linea and (not "Settings" in linea) and ("Fc") in linea:
            Active  = linea[11:14].strip()
            Fc      = linea[28:34].strip().replace(",",".")
            Gain    = linea[44:49].strip().replace(",",".")
            Q       = linea[56:61].strip().replace(",",".")
            # convertimos Q en BW(oct)
            BW = str(q2bw(float(Q)))[:6]
            # traducimos Active ON|OFF => 1|0
            if Active == "ON":
                Active = "1"
            else:
                Active = "0"
            lista.append((Active, Fc, Gain, Q, BW))

    # ordenamos ascendente por Frecuencias
    return sorted(lista, key=lambda filtro:float(filtro[1]))

def lista2ini(listaQuintupletas):
    """ traduce cada quintupleta [Active, Fc, Gain, Q, BW] de la lista de filtros 
        en una linea de texto de tipo INI"
    """
    listaFiltrosINI = []
    n = 1
    for f in listaQuintupletas:
        listaFiltrosINI.append("f" + str(n).ljust(2) + "      = " + f[0] + "   " + f[1].rjust(7) \
                               +  f[4].rjust(10)  + f[2].rjust(8) + "\n")
        n += 1
    return listaFiltrosINI

def hacerINI():
    """ Construye un INI utilizable por el módulo del FIRtro ecasound_PEQ_net.py
        con los filtros paramétricos de los dos canales de un altavoz.
    """
    # vamos construyendo el INI
    ini =  "\n#    Active:     Frec:  BW(oct):   Gain:" + "\n"

    # leemos el archivo con la lista de filtros de cada canal
    for fname in [fLeft, fRight]:
        if "L" in fname: seccion = "[left]"
        else:            seccion = "[right]"
        
        # escribimos le sección del ini para el canal en curso
        ini += "\n" + seccion + "\n"
        
        filtros = lista2ini(tabulaREW(leeREW(fname))) # fname es el REW.txt de un canal
        # ^^ OjO son muchos filtros seguidos
        #    SIN EMBARGO cada plugin admite 4 filtros
        
        if len(filtros) > 0:
            hay_filtros = True

        n = 1 # contador de plugins
        while hay_filtros:
            
            # insertamos los valores globales del plugin
            ini +=  "global" + str(n).ljust(2) + " = 1                         0.0\n"
            
            for p in range(4): # hacemos un paquete de 4 filtros por plugin
                
                try: # escribinos un filtro si lo hay o un filtro fake (desactivado) de relleno
                    f = filtros.pop(0)
                    ini += f
                    last_f = int(f[1:3]) 
                except:
                    ini += "f" + str(last_f + 1).ljust(2) + "      = 0        10    1.0        0.0\n"
                    hay_filtros = False
                    last_f += 1
            n += 1
        
    return ini

if __name__ == '__main__':

    try:
        fRight = sys.argv[2]
        fLeft  = sys.argv[1]
        print hacerINI()

    except:
        print __doc__


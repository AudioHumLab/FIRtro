#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" rutina de chequeo de un comando
    v.0.0.1
"""
from time import sleep
from subprocess import check_output

def wait4result(comando, respuesta, tmax=4, quiet=False):
    """ Verifica que se reciba la cadena "respuesta" al enviar el "comando".
        Por ejemplo "mplayer:out_0" al enviar "jack_lsp"
    """
    # esperamos hasta tmax segundos salvo si hay respuesta al comando:
    intentos =  20
    trefresco = float(tmax) / intentos
    while intentos:
        try:
            if respuesta in check_output(comando, shell=True):
                if not quiet:
                    print "(wait4) se ha verificado  '" + respuesta + "' en '" + comando + "'"
                break
        except:
            pass
        intentos -= 1
        sleep(trefresco)
    
    if intentos:
        return True
    else:
        if not quiet:
            print "(wait4) Time out > " + str(tmax) + "s verificando '" + respuesta + "' en '" + comando + "'"
        return False
        
if __name__ == "__main__":
    print __doc__


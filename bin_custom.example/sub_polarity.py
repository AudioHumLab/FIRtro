#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
cambia la polaridad del subwoofer
"""

import sys, os
import socket

import ConfigParser

########################
salidaSub = "sw_1"     #
########################

def bf_cli (orden):
    bfHost= "localhost"
    bfPort= "3000"
    try:
        s = socket.socket()
        s.connect((bfHost, int(bfPort)))
        s.send(orden + "\n")
        s.close()
    except socket.error, (value, msg):
        s.close()
        error = "Brutefir: " + "[Errno " + str(value) +"] " + msg

def ajustaPol():

    # OjO para ajustar la polaridad, parece ser que hay que configurar el filter en dos veces,
    # no lo he conseguido en una sola orden sin que se pierda la atenuacion ¿?
    
    # la primera vez con la polaridad:
    tmp = 'cfoa "f_' + salidaSub + '" "' + salidaSub + '" M' + pol + '; quit;'
    bf_cli(tmp)

    # y la segunda con la atenuacion:
    #atenSub = buscaAtenSub()
    tmp = 'cfoa "f_' + salidaSub + '" "' + salidaSub + '" ' + atenSub + '; quit;'
    bf_cli(tmp)

def buscaAtenSub():
    bfIni = ConfigParser.ConfigParser()
    bfIni.read("/home/firtro/audio/brutefir.ini")
    paramsSub = bfIni.get("outputs", salidaSub)
    atenSub = paramsSub.split()[1]
    return atenSub

if __name__ == "__main__":

    pol = "1" # por defecto
    if len(sys.argv) > 1:
        atenSub = sys.argv[1]
        pol = sys.argv[2]
    ajustaPol()

    # mostramos como ha quedado
    os.system('lf')



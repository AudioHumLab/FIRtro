#!/usr/bin/env python
# -*- coding: utf-8 -*-

# v1.1
# eliminamos time.sleep, usamos un bucle para recibir datos

from sys import argv as sys_argv
import socket

def bfcli(comando):
    """ para enviar comandos a Brutefir y recibir resultados
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(('localhost', 3000))
    s.send(comando + "\n")
    respuesta = ""
    while True:    
        recibido = s.recv(4096)
        if recibido:
            respuesta += recibido
        else:
            break
    s.close()
    # print respuesta # DEBUG
    return respuesta

if __name__ == '__main__':
    try:
        comando = ";".join(sys_argv[1:]) + ";"
        print bfcli(comando)
    except:
        "algo va mal :-("

#!/usr/bin/env python
# -*- coding: utf-8 -*-

from sys import argv as sys_argv
from time import sleep
import socket

def bfcli(comando):
    """ para enviar comandos a Brutefir y recibir resultados
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(('localhost', 3000))
    s.send(comando + "\n")
    sleep(.2)
    data = s.recv(4096)
    s.close()
    return data

if __name__ == '__main__':
    try:
        comando = ";".join(sys_argv[1:]) + ";"
        print bfcli(comando)
    except:
        "algo va mal :-("

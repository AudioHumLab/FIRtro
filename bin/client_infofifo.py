#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
    Módulo auxiliar para comunicar con el servidor de INFOFIFO (server_infofifo.py)
"""

from time import sleep
import socket
infofifo_socket = None

def cmd(cmd):
    # envía y recibe (SIN USO en server_infofifo.py)
    infofifo_socket.send(cmd + '\n')
    answer = infofifo_socket.recv(1024).strip('\n')
    return answer

def cmd_s(cmd):
    # solo enviar sin recibir
    infofifo_socket.send(cmd)

def open(server="localhost:9995"):
    infofifo_host, infofifo_port = server.split(":")
    infofifo_port = int(infofifo_port)
    global infofifo_socket
    # Abrimos un socket al server
    try:
        infofifo_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Nos conectamos
        infofifo_socket.connect((infofifo_host, infofifo_port))
        sleep(.1)
        return True
    except:
        print "(client_infofifo) ERROR conectando a " + server
        infofifo_socket.close()
        return False

def close():
    # Cancela el cliente en el server de FIFO
    infofifo_socket.close()

if __name__ == "__main__":

    print __doc__

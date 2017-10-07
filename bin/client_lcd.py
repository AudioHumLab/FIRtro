#!/usr/bin/python
# -*- coding: utf-8 -*-
""" 
    Módulo para comunicar con un servidor LCDproc
"""

# v1.0
# - Desgajado de server_lcdproc.py
# - Se escribe este modulo para ser usado por cualquiera que 
#   quiera acceder al servidor LCDproc

import re
import socket
lcdproc_socket = None

def cmd(cmd):
    # envía y recibe de LCDd
    lcdproc_socket.send(cmd + '\n')
    answer = lcdproc_socket.recv(1024).strip('\n')
    return answer

def cmd_s(cmd):
    # solo enviar sin recibir es más rapido
    lcdproc_socket.send(cmd + '\n')

def open(client_name, server="localhost:13666"):
    lcdproc_host, lcdproc_port = server.split(":")
    lcdproc_port = int(lcdproc_port)
    global lcdproc_socket
    # Abrimos un socket al server
    try:
        lcdproc_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Nos conectamos
        lcdproc_socket.connect((lcdproc_host, lcdproc_port))
    except:
        # print 'Error conectandose a lcdproc'
        lcdproc_socket.close()
        return False

    global hello_answer
    hello_answer = cmd('hello')
    #print hello_answer
    if not "huh?" in hello_answer:
        #print "registrando cliente: " + client_name
        cmd_s('client_set name ' + client_name)
        return True
    else:
        return False

def get_size():
    lcd_hgt = int(re.sub(' .*', '', re.sub('.* hgt ', '', hello_answer)))
    lcd_wid = int(re.sub(' .*', '', re.sub('.* wid ', '', hello_answer)))
    return lcd_hgt, lcd_wid

def close():
    # Cancela el cliente en el server LCDd
    lcdproc_socket.close()

def delete_screen(sname):
    cmd_s('screen_del ' + sname)

def create_screen(sname, priority="info", duration=3, timeout=0):
    # duration: A screen will be visible for this amount of time every rotation (1/8 sec)
    # timeout:  After the screen has been visible for a total of this amount of time,
    #           it will be deleted (1/8 sec)
    cmd_s('screen_add ' + sname)
    dur = str(duration * 8)
    tou = str(timeout  * 8)
    tmp = 'screen_set ' + sname + " -cursor no"
    cmd_s(tmp); #print "(server_lcd_big)  tmp" # para debug
    tmp = 'screen_set ' + sname + ' priority ' + priority
    cmd_s(tmp); #print "(server_lcd_big)  tmp" # para debug
    if dur <> "0":
        tmp = 'screen_set ' + sname + ' duration ' + dur
        cmd_s(tmp); #print "(server_lcd_big)  tmp" # para debug
    if tou <> "0":
        tmp = 'screen_set ' + sname + ' timeout ' + tou
        cmd_s(tmp); #print "(server_lcd_big)  tmp" # para debug

# 0. CREACIÓN del cliente conectado al servidor LCDc
def crea_cliente(cname="biglevel", server="localhost:13666"):
    if open(cname, server):
        return get_size()
    else:
        return False

if __name__ == "__main__":

    print __doc__

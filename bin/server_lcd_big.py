#!/usr/bin/python
# -*- coding: utf-8 -*-

# v1.0

# Colección de iconos disponiles:
# https://github.com/lcdproc/lcdproc/blob/master/server/widget.c
# NOTA: Cuando se dibujan widgets 'num' (numeros gordos) los widget 'icon' se cuartean :-/
#       No hay buena compatibilidad usando 'num' con 'icon', usaremos 'string'.

import subprocess as sp
from time import sleep
from sys import argv as sys_argv

# http://lcdproc.sourceforge.net/docs/current-dev.html
import socket
import re
import time
import json
lcdproc_host = 'localhost'
lcdproc_port = 13666
lcdproc_socket = None

def split_by_n( seq, n ):
    # A generator to divide a sequence into chunks of n units
    while seq:
        yield seq[:n]
        seq = seq[n:]

def lcd_cmd(cmd):
    lcdproc_socket.send(cmd + '\n')
    lcdproc_out = lcdproc_socket.recv(1024).strip('\n')
    return lcdproc_out

def lcd_cmd_s(cmd):
    # solo enva es ms rápido
    lcdproc_socket.send(cmd + '\n')

def lcd_open(client_name):
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
    hello_answer = lcd_cmd('hello')
    #print hello_answer
    if not "huh?" in hello_answer:
        #print "registrando cliente: " + client_name
        lcd_cmd_s('client_set name ' + client_name)
        return True
    else:
        return False

def lcd_get_size():
    lcd_hgt = int(re.sub(' .*', '', re.sub('.* hgt ', '', hello_answer)))
    lcd_wid = int(re.sub(' .*', '', re.sub('.* wid ', '', hello_answer)))
    return lcd_hgt, lcd_wid

def lcd_close():
    # OjO esto cancelará el cliente en el server LCDd
    lcdproc_socket.close()

def show_level(x):
    create_screen()
    cad = str(x)

    if cad and not "-" in cad:
        cad = "+" + cad
    i = 1
    for c in cad:
        if c.isdigit():
            lcd_cmd_s('widget_add vol dig' + str(i) + ' num')
            lcd_cmd_s('widget_set vol dig' + str(i) + ' ' + str(i*3) + ' '  + c)
        elif c == ".":
            lcd_cmd_s('widget_add vol dot     string')
            lcd_cmd_s('widget_set vol dot  ' + str(i*3) + ' 4 "#"')
        elif c == "-":
            draw_minus()
        elif c == "+":
            draw_plus()
        i += 1

def create_screen():
    lcd_cmd_s('screen_del vol')
    lcd_cmd_s('screen_add vol')
    lcd_cmd_s('screen_set -name vol -priority foreground')

def draw_minus():
    for i in 1,2,3:
        lcd_cmd_s('widget_add vol minus' + str(i) + '  string')
        lcd_cmd_s('widget_set vol minus' + str(i) + ' ' + str(i) + ' 3 "#"')

def draw_plus():
    for i in 1,2,3,4,5:
        lcd_cmd_s('widget_add vol plus' + str(i) + '   string')
    lcd_cmd_s('widget_set vol plus1   2 2 "#"')
    lcd_cmd_s('widget_set vol plus2   1 3 "#"')
    lcd_cmd_s('widget_set vol plus3   2 3 "#"')
    lcd_cmd_s('widget_set vol plus4   3 3 "#"')
    lcd_cmd_s('widget_set vol plus5   2 4 "#"')

def crea_cliente(cname="big"):
    if lcd_open(cname):
        #print "tamaño:", lcd_get_size()
        pass

if __name__ == "__main__":

    crea_cliente("tmp")

    vol = ""
    if len(sys_argv) > 1:
        vol = float(sys_argv[1])

        show_level(vol)

#!/usr/bin/python
# -*- coding: utf-8 -*-

# v1.0a
# - se añade MUTE si mute=True en show_level()

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
    answer = lcdproc_socket.recv(1024).strip('\n')
    return answer

def lcd_cmd_s(cmd):
    # solo enviar sin recibir es más rapido
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
    # Cancela el cliente en el server LCDd
    lcdproc_socket.close()

def _draw_level(cad):
    # recorre la cadena y pinta +/-, dígitos y punto decimal
    
    # añade un '+' en las cadenas de valores positivos
    if cad and not "-" in cad:
        cad = "+" + cad
    i = 1
    for c in cad:
        if c.isdigit():
            _draw_big_digits(digit=c, pos=i)
        elif c == ".":
            _draw_dot(pos=i)
        elif c == "-":
            _draw_minus()
        elif c == "+":
            _draw_plus()
        i += 1

def _delete_screen(sname):
    lcd_cmd_s('screen_del ' + sname)

def _create_screen(sname):
    lcd_cmd_s('screen_add ' + sname)
    lcd_cmd_s('screen_set -name ' + sname + '  -priority foreground')

def _draw_big_digits(digit, pos):
    lcd_cmd_s('widget_add level dig' + str(pos) + ' num')
    lcd_cmd_s('widget_set level dig' + str(pos) + ' ' + str(pos*3) + ' '  + digit)

def _draw_dot(pos):
    lcd_cmd_s('widget_add level dot     string')
    lcd_cmd_s('widget_set level dot  ' + str(pos*3) + ' 4 "#"')

def _draw_minus():
    for i in 1,2,3:
        lcd_cmd_s('widget_add level minus' + str(i) + '  string')
        lcd_cmd_s('widget_set level minus' + str(i) + ' ' + str(i) + ' 2 "#"')

def _draw_plus():
    for i in 1,2,3,4,5:
        lcd_cmd_s('widget_add level plus' + str(i) + '   string')
    lcd_cmd_s('widget_set level plus1   2 1 "#"')
    lcd_cmd_s('widget_set level plus2   1 2 "#"')
    lcd_cmd_s('widget_set level plus3   2 2 "#"')
    lcd_cmd_s('widget_set level plus4   3 2 "#"')
    lcd_cmd_s('widget_set level plus5   2 3 "#"')

def _draw_mute():
    # Nota: la \ no funciona
    #     12345678901234567890
    l1 = " _   _      ___  __"
    l2 = "| | / | | |  |  |  "
    l3 = "|  V  | | |  |  |- "
    l4 = "|     |  V   |  |__"
    lineas = l1, l2, l3, l4
    _draw_lineas(lineas, screen="mute")

def _draw_lineas(lineas, screen):
    # como widget_set no admite strings con espacios en blanco,
    # troceamos las lineas en string de 1 caracter para poder
    # visualizar una composición manual a base de 4 líneas
    i = 0
    for fila in range(1, 5):
        lin = lineas[i]
        troceador = split_by_n(lin, 1)
        for col in range(1, 21):
            lcd_cmd_s('widget_add ' + screen + ' mute_' + str(col) + '_' + str(fila) + '  string')
            try:
                c = troceador.next()
                lcd_cmd_s('widget_set ' + screen + ' mute_' + str(col) + '_' + str(fila) \
                          + ' ' + str(col) + ' ' + str(fila) + ' ' + c)
            # se ha agotado el generator de troceo:
            except:
                pass
        i += 1

def show_level(level, muted=False):
    # Funcion principal a usar una vez creado el cliente con crea_cliente()
    # MUTED
    if muted:
        _delete_screen("level")
        _delete_screen("mute")
        _create_screen("mute")
        _draw_mute()
    # NORMAL
    else:
        _delete_screen("mute")
        _delete_screen("level")
        _create_screen("level")
        _draw_level( str(level) )

def crea_cliente(cname="biglevel"):
    # Creación del cliente conectado al servidor LCDc
    if lcd_open(cname):
        return lcd_get_size()
    else:
        return False

if __name__ == "__main__":
    crea_cliente("tmp")
    vol = ""
    if len(sys_argv) > 1:
        vol = float(sys_argv[1])
        show_level(vol)

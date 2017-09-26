#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
    Letras grandes en el LCD.
    Pruebas en línea de comandos:
        server_lcd_big.py   -l level_a_mostrar
                            -m mensaje
    (el cliente expira en 10 seg)
"""

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

# custom module
import lcdbig

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
    """ recorre la cadena y pinta +/-, dígitos y punto decimal """
    _delete_screen("mute")
    _delete_screen("level")
    _create_screen("level")

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

def _create_screen(sname, timeout=3):
    # NOTA el timeout es el tiempo visible luego se borrara la screen
    #      PEEEEERO no se borra ¿!?
    timeout = str(timeout * 8) # el comando se debe dar al server en 1/8 sec
    lcd_cmd_s('screen_add ' + sname)
    lcd_cmd_s('screen_set -name ' + sname + '  -priority foreground -timeout ' + timeout)

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
    l4 = "|     | L_|  |  |__"
    lineas = l1, l2, l3, l4

    _delete_screen("level")
    _delete_screen("mute")
    _create_screen("mute")
    _draw_lineas(lineas, screen="mute")

def _draw_lineas(lineas, screen, coloffset=1):
    """toma 4 lineas de texto y la pinta en estático, admite un offset de columnas
    """
    # como widget_set no admite strings con espacios en blanco,
    # troceamos las lineas en string de 1 caracter para poder
    # visualizar una composición manual a base de 4 líneas
    i = 0
    for fila in range(1, 5):
        lin = lineas[i]
        troceador = split_by_n(lin, 1)
        for col in range(coloffset, 21):
            wID = 'w_' + str(col) + '_' + str(fila)
            lcd_cmd_s('widget_add ' + screen + ' ' + wID + ' string')
            try:
                c = troceador.next()
                lcd_cmd_s('widget_set ' + screen + ' ' + wID + ' ' \
                          + str(col) + ' ' + str(fila) + ' ' + c)
            # se ha agotado el generator de troceo:
            except:
                pass
        i += 1

def _draw_lineas_scroller(lineas, screen, coloffset=1, speed="1"):
    """toma 4 lineas de texto y la pinta en scroll
    """
    for i in range(1,5):
        wID = 'w_' + str(i)
        lcd_cmd_s('widget_add ' + screen + ' ' + wID + ' scroller')

    i = 1
    for linea in lineas:
        linea = linea.replace(" ", "\ ")
        wID = 'w_' + str(i)
        lcd_cmd_s('widget_set ' + screen + ' ' + wID + ' ' + \
                  '1 ' + str(i) + ' 20 ' + str(i) + ' m ' + str(speed) + ' ' + linea)
        i += 1

def show_big_scroller(cad="test string toooo long" , speed="1", timeout=5):
    for s in "mute", "level":
        _delete_screen(s)
    sname = "bigscroller"
    _delete_screen(sname)
    _create_screen(sname, timeout=timeout)
    acum = ["", "", "", ""]
    for c in cad + " ":
        c1,c2,c3,c4 = lcdbig.wbig3(c)
        acum[0] += c1
        acum[1] += c2
        acum[2] += c3
        acum[3] += c4
    _draw_lineas_scroller( acum, sname, speed=speed)

def _pba_big(cad="hola", screen="prueba"):
    # PRUEBA para usar los BigWidgets
    for s in "mute", "level":
        _delete_screen(s)
    _delete_screen(screen)
    _create_screen(screen)
    i = 1
    for c in cad:
        _draw_lineas( lcdbig.wbig3(c), screen, coloffset=i)
        i += 3

def _pba_ver_chars(screen="prueba"):
    # CUTRE prueba para imprimir  80 posibles caracteres empezando por chr(i)
    for s in "mute", "level":
        _delete_screen(s)
    _delete_screen(screen)
    _create_screen(screen)
    i = 32
    for fila in range(1, 5):
        for col in range(1, 21):
            lcd_cmd_s('widget_add ' + screen + ' p_' + str(col) + '_' + str(fila) + '  string')
            c = chr(i)
            lcd_cmd_s('widget_set ' + screen + ' p_' + str(col) + '_' + str(fila) \
                          + ' ' + str(col) + ' ' + str(fila) + ' ' + c)
            i += 1

def show_level(level, muted=False):
    # Funcion principal a usar una vez creado el cliente con crea_cliente()
    if muted:
        _draw_mute()
    else:
        _draw_level( str(level) )

def crea_cliente(cname="biglevel"):
    # Creación del cliente conectado al servidor LCDc
    if lcd_open(cname):
        return lcd_get_size()
    else:
        return False

if __name__ == "__main__":

    if len(sys_argv) == 3:
        modo = sys_argv[1]
        mens = sys_argv[2]
        crea_cliente("tmp")
        if modo == "-l":
            vol = float(mens)
            show_level(vol)
        elif modo == "-m":
            show_big_scroller(mens)
        sleep(10)
    else:
        print __doc__

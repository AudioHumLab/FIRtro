#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
    Letras grandes en el LCD.
    Pruebas en línea de comandos:
        server_lcd_big.py   -l level_a_mostrar
                            -m mensaje
    (el cliente de prueba expira en 10 seg)
"""

# v1.0a
# - Se añade MUTE si mute=True en show_level()
# v1.0b
# - Disponible un scroll a pantalla completa que muestra una cadena de texto usando
#   las rutinas de lcdbig.py que escalan los caracteres mediante un artificio a base de
#   4 lineas de caracteres ascii básicos, ya que LCDproc no admite ascii extendido.
# v1.0c
# - Se separan las funiones básicas de interacción con el server LCDproc
#   en un módulo comun 'client_lcd.py', que se importa aquí.

# Colección de iconos disponiles LCDproc:
# https://github.com/lcdproc/lcdproc/blob/master/server/widget.c
# NOTA: Cuando se dibujan widgets 'num' (numeros gordos) los widget 'icon' se cuartean :-/
#       No hay buena compatibilidad usando 'num' con 'icon', usaremos 'string'.

from time import sleep
from sys import argv as sys_argv

# módulo base para interactuar con un servidor LCDproc:
import client_lcd as lcd
# módulo auxiliar para escalar caracteres en 4 lineas:
import lcdbig

def split_by_n( seq, n ):
    # A generator to divide a sequence into chunks of n units
    while seq:
        yield seq[:n]
        seq = seq[n:]

def _draw_big_digits(digit, pos):
    # auxiliar para la pantalla "level" con dígitos grandes 'num' nativos de LCDproc
    lcd.cmd_s('widget_add level dig' + str(pos) + ' num')
    lcd.cmd_s('widget_set level dig' + str(pos) + ' ' + str(pos*3) + ' '  + digit)

def _draw_dot(pos):
    # auxiliar para símbolo no contemplado en los dígitos grandes 'num' nativos de LCDproc
    lcd.cmd_s('widget_add level dot     string')
    lcd.cmd_s('widget_set level dot  ' + str(pos*3) + ' 4 "#"')

def _draw_minus():
    # auxiliar para símbolo no contemplado en los dígitos grandes 'num' nativos de LCDproc
    for i in 1,2,3:
        lcd.cmd_s('widget_add level minus' + str(i) + '  string')
        lcd.cmd_s('widget_set level minus' + str(i) + ' ' + str(i) + ' 2 "#"')

def _draw_plus():
    # auxiliar para símbolo no contemplado en los dígitos grandes 'num' nativos de LCDproc
    for i in 1,2,3,4,5:
        lcd.cmd_s('widget_add level plus' + str(i) + '   string')
    lcd.cmd_s('widget_set level plus1   2 1 "#"')
    lcd.cmd_s('widget_set level plus2   1 2 "#"')
    lcd.cmd_s('widget_set level plus3   2 2 "#"')
    lcd.cmd_s('widget_set level plus4   3 2 "#"')
    lcd.cmd_s('widget_set level plus5   2 3 "#"')

def _draw_level(cad, screen="level", priority="info", duration=3):
    # recorre la cadena y pinta +/-, dígitos y punto decimal
    lcd.delete_screen("mute")
    lcd.delete_screen(screen)
    lcd.create_screen(screen, priority=priority, duration=duration)

    # añade un '+' para pintarlo en caso de valor positivo
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

def _draw_mute(priority="info"):
    # Nota: la \ no funciona
    #     12345678901234567890
    l1 = " _   _      ___  __"
    l2 = "| | / | | |  |  |  "
    l3 = "|  V  | | |  |  |- "
    l4 = "|     | \_|  |  |__"
    lineas = l1, l2, l3, l4

    lcd.delete_screen("level")
    lcd.delete_screen("mute")
    lcd.create_screen("mute", priority=priority)
    _draw_lineas(lineas, screen="mute")

def _draw_lineas(lineas, screen, coloffset=1):
    # Toma 4 lineas de texto y la pinta en estático, admite un offset de columnas
    # Nota: como widget_set no admite strings con espacios en blanco,
    #       troceamos las lineas en string de 1 caracter para poder
    #       visualizar una composición manual a base de 4 líneas
    i = 0
    for fila in range(1, 5):
        lin = lineas[i]
        troceador = split_by_n(lin, 1)
        for col in range(coloffset, 21):
            wID = 'w_' + str(col) + '_' + str(fila)
            lcd.cmd_s('widget_add ' + screen + ' ' + wID + ' string')
            try:
                c = troceador.next()
                lcd.cmd_s('widget_set ' + screen + ' ' + wID + ' ' \
                          + str(col) + ' ' + str(fila) + ' ' + c)
            # se ha agotado el generator de troceo:
            except:
                pass
        i += 1

def _draw_lineas_scroller(lineas, screen, speed="1"):
    # Toma 4 lineas de texto y la pinta en scroll
    for i in range(1,5):
        wID = 'w_' + str(i)
        lcd.cmd_s('widget_add ' + screen + ' ' + wID + ' scroller')

    i = 1
    for linea in lineas:
        linea = linea.replace(" ", "\ ")
        wID = 'w_' + str(i)
        lcd.cmd_s('widget_set ' + screen + ' ' + wID + ' ' + \
                  '1 ' + str(i) + ' 20 ' + str(i) + ' m ' + str(speed) + ' ' + linea)
        i += 1

def _pba_big(cad="hola son la 12:34", screen="prueba"):
    # PRUEBA para usar los BigWidgets de lcdbig.py
    for s in "mute", "level":
        lcd.delete_screen(s)
    lcd.delete_screen(screen)
    lcd.create_screen(screen)
    i = 1
    for c in cad:
        _draw_lineas( lcdbig.wbig3(c), screen, coloffset=i)
        i += 3

def _pba_ver_chars(screen="prueba"):
    # CUTRE prueba para imprimir  80 posibles caracteres empezando por chr(i)
    for s in "mute", "level":
        lcd.delete_screen(s)
    lcd.delete_screen(screen)
    lcd.create_screen(screen)
    i = 32
    for fila in range(1, 5):
        for col in range(1, 21):
            lcd.cmd_s('widget_add ' + screen + ' p_' + str(col) + '_' + str(fila) + '  string')
            c = chr(i)
            lcd.cmd_s('widget_set ' + screen + ' p_' + str(col) + '_' + str(fila) \
                          + ' ' + str(col) + ' ' + str(fila) + ' ' + c)
            i += 1

# 1. Funcion principal que muestra un LEVEL con los números grandes nativos de LCDproc.
#    También mostrará MUTE según la prioridad especificada.
def show_level(level="-12.34", muted=False, screen="level",  \
               level_priority="info", mute_priority="info", duration=3):
    # Muestra un float de level usando el widget grande 'num' nativo de lcdproc
    # excepto en estado mute, que se pintará la pantalla estática MUTE.
    if not muted:
        _draw_level( level, screen, level_priority, duration=duration )
    else:
        _draw_mute(priority=mute_priority)

# 2. Función principal que muestra una cadena de texto
#    en un scroller a pantalla completa.
def show_big_scroller(cad="ejemplo de texto largo" , speed="1", \
                      priority="info", duration=10, timeout=0, screen="bigscroller"):
    lcd.delete_screen(screen)
    lcd.create_screen(screen, priority=priority, duration=duration , timeout=timeout)
    acum = ["", "", "", ""]
    for c in cad + " ":
        #c1,c2,c3,c4 = lcdbig.wbig3(c)
        #acum[0] += c1
        #acum[1] += c2
        #acum[2] += c3
        #acum[3] += c4
        acum = [ "".join(x) for x in zip( acum, lcdbig.wbig3(c) ) ]
    _draw_lineas_scroller( acum, screen, speed=speed)

# 0. CREACIÓN del cliente conectado al servidor LCDc
def crea_cliente(cname="biglevel", server="localhost:13666"):
    if lcd.open(cname, server):
        return lcd.get_size()
    else:
        return False

if __name__ == "__main__":

    if len(sys_argv) == 3:
        modo = sys_argv[1]
        mens = sys_argv[2]
        crea_cliente("tmp")
        if modo == "-l":
            show_level(mens, screen="tmp", priority="foreground")
        elif modo == "-m":
            show_big_scroller(mens, screen="tmp", priority="foreground")
        sleep(10)
    else:
        print __doc__

#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
    Uso interno.
    Rutinas para presentar texto grande a pantalla completa:
    - Texto expandido en 4 lineas de altura, en scroller.
    - Dígitos grandes para visualizar el volumen.
    - 'MUTE' en tamaño grande 
"""
# v1.1
# - se incorporan aquí las rutinas para hacer scroller de texto de altura 4,
#   para mostrar el volumen con dígitos grandes,
#   y para presentar 'MUTE' con caracteres grandes.

# NOTAS: 
#   - El backslash '\' NO es printable por parte del server, ni siquiera escapado.
#   - Solo se permite el uso de caracteres ascii básicos, no extendidos.
#   - Colección de iconos disponiles LCDproc:
#       https://github.com/lcdproc/lcdproc/blob/master/server/widget.c
#   - Cuando se dibujan widgets 'num' (numeros gordos) los widget 'icon' se cuartean :-/
#       No hay buena compatibilidad usando 'num' con 'icon', usaremos 'string'.

import client_lcd as cLCD

def wbig3(c):
    """ devuelve 4 cadenas de ancho 3 para pintar
        un widget de un caracter grande en el LCD
    """
    c = c.lower()

    mis1 = [",", ".", ";", ":"]
    mis2 = [" ", "_", "-", "+", "*", "/", "=", "[", "]", "(", ")"]

    # ANCHO 3 es difíl de representar pero es preferible en LCD de 20x4
    # ya que caben más caracteres en una pantalla LCD de ancho 20
    #       123 123 123 123 123 123 123 123 123 123
    l01 =  " _       _   _   _   __  _             "
    l02 =  "|_| |_  /   | | |_  |_  |   |_|  |    |"
    l03 =  "| | |_| |_  |_/ |_  |   |_] | |  |  |_|"
    l04 =  "                                       "
    #       123 123 123 123 123 123 123 123 123 123
    l11 =  "                 _   _   _   _   _  ___"
    l12 =  "|_/ |   |^| |/| | | |_) |_| |_) (_   | "
    l13 =  "| | |__ | | | | |_| |     | ||   _)  | "
    l14 =  "                                       "
    #       123 123 123 123 123 123 123 123 123 123
    l21 =  "                    __                 "
    l22 =  "| | | / | / |/  |_/  /           .   . "
    l23 =  "|_| |/  |X/ /|   |  /_   ,   .   ,   . "
    l24 =  "                                       "
    #       123 123 123 123 123 123 123 123 123 123
    l31 =  " _       _   _       _      __   _   _ "
    l32 =  "| |  /|  _|  _) |_| |_   /   /  (_) (_)"
    l33 =  "|_|   | (_   _)   | __) (_) /   (_)  / "
    l34 =  "                                       "
    #       123 123 123 123 123 123 123 123 123 123 123
    l41 =  "                              _ _          "
    l42 =  "         -   +   *   /   -   |   |         "
    l43 =  "    ___                  -   |_ _|   (   ) "
    l44 =  "                                           "

    # letras
    if   ord(c) in range(97,107):
        col = (ord(c) - 97) * 4
        c1 = l01[col:col+3]
        c2 = l02[col:col+3]
        c3 = l03[col:col+3]
        c4 = l04[col:col+3]
    elif ord(c) in range(107,117):
        col = (ord(c) - 107) * 4
        c1 = l11[col:col+3]
        c2 = l12[col:col+3]
        c3 = l13[col:col+3]
        c4 = l14[col:col+3]
    elif ord(c) in range(117,123):
        col = (ord(c) - 117) * 4
        c1 = l21[col:col+3]
        c2 = l22[col:col+3]
        c3 = l23[col:col+3]
        c4 = l24[col:col+3]
    # digitos
    elif ord(c) in range(48,58):
        col = (ord(c) - 48) * 4
        c1 = l31[col:col+3]
        c2 = l32[col:col+3]
        c3 = l33[col:col+3]
        c4 = l34[col:col+3]
    # simbolos
    elif c in mis1:
        col = (mis1.index(c) + 6) * 4
        c1 = l21[col:col+3]
        c2 = l22[col:col+3]
        c3 = l23[col:col+3]
        c4 = l24[col:col+3]
    elif c in mis2:
        col = mis2.index(c) * 4
        c1 = l41[col:col+3]
        c2 = l42[col:col+3]
        c3 = l43[col:col+3]
        c4 = l44[col:col+3]

    else:
        c1=c2=c3=c4=""

    return c1,c2,c3,c4


def wbig4(c):
    """ devuelve 4 cadenas de ancho 4 para pintar
        un widget de un caracter grande en el LCD
    """
    c = c.lower()

    mis1 = [",", ".", ";", ":"]
    mis2 = [" ", "_", "-", "+", "*", "/", "=", "[", "]", "(", ")"]

    # ANCHO 4, ocupa demasiado en 20x4 !!!
    # (i) Podría ser de interés con un display de 40x4
    
    #       1234 1234 1234 1234 1234 1234 1234 1234 1234 1234
    l01 =  " __   __   __   __   __   __   __               _"
    l02 =  "|__| |__/ |    |  \ |_   |_   | _  |__|  |      |"
    l03 =  "|  | |__| |__  |__| |__  |    |__) |  |  |   |__|"
    l04 =  "                                                 "
    #       1234 1234 1234 1234 1234 1234 1234 1234 1234 1234
    l11 =  "                     __   __   __   __   __  ___ "
    l12 =  "|__/ |    |\/| |\ | |  | |__) |  | |__) (__   |  "
    l13 =  "|  \ |___ |  | | \| |__| |    |_\| | \   __)  |  "
    l14 =  "                                                 "
    #       1234 1234 1234 1234 1234 1234 1234 1234 1234 1234
    l21 =  "                          __                     "
    l22 =  "|  | | /  \ /   \/   \ /   /              .    . "
    l23 =  "|__| |/   \X/   /\    |   /_    ,    ,    ,    . "
    l24 =  "                                                 "
    #       1234 1234 1234 1234 1234 1234 1234 1234 1234 1234
    l31 =  " _         _    _         __        __   _    _  "
    l32 =  "| |   /|   _|   _)  |_|  |_     /    /  (_)  (_) "
    l33 =  "|_|    |  (_    _)    |  __)   (_)  /   (_)   /  "
    l34 =  "                                                 "
    #       1234 1234 1234 1234 1234 1234 1234 1234 1234 1234 1234
    l41 =  "                 |         /   __    _   _            "
    l42 =  "           --   ---   X   /    __   |     |    (   )  "
    l43 =  "      __         |       /          |_   _|    (   )  "
    l44 =  "                                                      "

    # letras
    if   ord(c) in range(97,107):
        col = (ord(c) - 97) * 4
        c1 = l01[col:col+3]
        c2 = l02[col:col+3]
        c3 = l03[col:col+3]
        c4 = l04[col:col+3]
    elif ord(c) in range(107,117):
        col = (ord(c) - 107) * 4
        c1 = l11[col:col+3]
        c2 = l12[col:col+3]
        c3 = l13[col:col+3]
        c4 = l14[col:col+3]
    elif ord(c) in range(117,123):
        col = (ord(c) - 117) * 4
        c1 = l21[col:col+3]
        c2 = l22[col:col+3]
        c3 = l23[col:col+3]
        c4 = l24[col:col+3]
    # digitos
    elif ord(c) in range(48,58):
        col = (ord(c) - 48) * 4
        c1 = l31[col:col+3]
        c2 = l32[col:col+3]
        c3 = l33[col:col+3]
        c4 = l34[col:col+3]
    # simbolos
    elif c in mis1:
        col = (mis1.index(c) + 6) * 4
        c1 = l21[col:col+3]
        c2 = l22[col:col+3]
        c3 = l23[col:col+3]
        c4 = l24[col:col+3]
    elif c in mis2:
        col = mis2.index(c) * 4
        c1 = l41[col:col+3]
        c2 = l42[col:col+3]
        c3 = l43[col:col+3]
        c4 = l44[col:col+3]

    else:
        c1=c2=c3=c4=""

    return c1,c2,c3,c4

def split_by_n( seq, n ):
    # A generator to divide a sequence into chunks of n units
    while seq:
        yield seq[:n]
        seq = seq[n:]

# Las funciones a continuación son de uso local y las nombramos '_xxxx'

def _draw_big_digits(digit, pos):
    # auxiliar para la pantalla "level" con dígitos grandes 'num' nativos de LCDproc
    cLCD.cmd_s('widget_add level dig' + str(pos) + ' num')
    cLCD.cmd_s('widget_set level dig' + str(pos) + ' ' + str(pos*3) + ' '  + digit)

def _draw_dot(pos):
    # auxiliar para símbolo no contemplado en los dígitos grandes 'num' nativos de LCDproc
    cLCD.cmd_s('widget_add level dot     string')
    cLCD.cmd_s('widget_set level dot  ' + str(pos*3) + ' 4 "#"')

def _draw_minus():
    # auxiliar para símbolo no contemplado en los dígitos grandes 'num' nativos de LCDproc
    for i in 1,2,3:
        cLCD.cmd_s('widget_add level minus' + str(i) + '  string')
        cLCD.cmd_s('widget_set level minus' + str(i) + ' ' + str(i) + ' 2 "#"')

def _draw_plus():
    # auxiliar para símbolo no contemplado en los dígitos grandes 'num' nativos de LCDproc
    for i in 1,2,3,4,5:
        cLCD.cmd_s('widget_add level plus' + str(i) + '   string')
    cLCD.cmd_s('widget_set level plus1   2 1 "#"')
    cLCD.cmd_s('widget_set level plus2   1 2 "#"')
    cLCD.cmd_s('widget_set level plus3   2 2 "#"')
    cLCD.cmd_s('widget_set level plus4   3 2 "#"')
    cLCD.cmd_s('widget_set level plus5   2 3 "#"')

def _draw_level(cad, screen="level", priority="info", duration=3):
    # recorre la cadena y pinta +/-, dígitos y punto decimal
    cLCD.delete_screen("mute")
    cLCD.delete_screen(screen)
    cLCD.create_screen(screen, priority=priority, duration=duration)

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

    cLCD.delete_screen("level")
    cLCD.delete_screen("mute")
    cLCD.create_screen("mute", priority=priority)
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
            cLCD.cmd_s('widget_add ' + screen + ' ' + wID + ' string')
            try:
                c = troceador.next()
                cLCD.cmd_s('widget_set ' + screen + ' ' + wID + ' ' \
                          + str(col) + ' ' + str(fila) + ' ' + c)
            # se ha agotado el generator de troceo:
            except:
                pass
        i += 1

def _draw_lineas_scroller(lineas, screen, speed="1"):
    # Toma 4 lineas de texto y la pinta en scroll
    for i in range(1,5):
        wID = 'w_' + str(i)
        cLCD.cmd_s('widget_add ' + screen + ' ' + wID + ' scroller')

    i = 1
    for linea in lineas:
        linea = linea.replace(" ", "\ ")
        wID = 'w_' + str(i)
        cLCD.cmd_s('widget_set ' + screen + ' ' + wID + ' ' + \
                  '1 ' + str(i) + ' 20 ' + str(i) + ' m ' + str(speed) + ' ' + linea)
        i += 1

def _pba_big(cad="hola son la 12:34", screen="prueba"):
    # PRUEBA para usar los BigWidgets de lcdbig.py
    for s in "mute", "level":
        cLCD.delete_screen(s)
    cLCD.delete_screen(screen)
    cLCD.create_screen(screen)
    i = 1
    for c in cad:
        _draw_lineas( lcdbig.wbig3(c), screen, coloffset=i)
        i += 3

def _pba_ver_chars(screen="prueba"):
    # CUTRE prueba para imprimir  80 posibles caracteres empezando por chr(i)
    for s in "mute", "level":
        cLCD.delete_screen(s)
    cLCD.delete_screen(screen)
    cLCD.create_screen(screen)
    i = 32
    for fila in range(1, 5):
        for col in range(1, 21):
            cLCD.cmd_s('widget_add ' + screen + ' p_' + str(col) + '_' + str(fila) + '  string')
            c = chr(i)
            cLCD.cmd_s('widget_set ' + screen + ' p_' + str(col) + '_' + str(fila) \
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
def show_scroller(cad="ejemplo de texto largo", screen="bigscroller", speed="1", \
                      priority="info", duration=10, timeout=0):
    cLCD.delete_screen(screen)
    cLCD.create_screen(screen, priority=priority, duration=duration , timeout=timeout)
    acum = ["", "", "", ""]
    for c in cad + " ":
        #c1,c2,c3,c4 = lcdbig.wbig3(c)
        #acum[0] += c1
        #acum[1] += c2
        #acum[2] += c3
        #acum[3] += c4
        acum = [ "".join(x) for x in zip( acum, wbig3(c) ) ]
    _draw_lineas_scroller( acum, screen, speed=speed)

if __name__ == "__main__":
    print __doc__



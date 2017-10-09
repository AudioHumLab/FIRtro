#!/usr/bin/python
# -*- coding: utf-8 -*-

# Rutinas para presentar texto grande a pantalla completa, en 4 líneas
# de caracteres ascii básicos, ya que LCDproc no admite ascii extendido.
#
# v0.2

# NOTAS: 
#   - El backslash '\' NO es printable por parte del server, ni siquiera escapado.
#   - Colección de iconos disponiles LCDproc:
#       https://github.com/lcdproc/lcdproc/blob/master/server/widget.c
#   - Cuando se dibujan widgets 'num' (numeros gordos) los widget 'icon' se cuartean :-/
#       No hay buena compatibilidad usando 'num' con 'icon', usaremos 'string'.


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

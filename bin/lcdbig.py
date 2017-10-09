#!/usr/bin/python
# -*- coding: utf-8 -*-

#v0.1 beta

# Rutina para presentar texto grande a pantalla completa, en 4 líneas
# de caracteres ascii básicos, ya que LCDproc no admite ascii extendido.
#
# NOTA: el backslash NO es printable por parte del server, 
#       ni siquiera escapado.

# !!! OJO array **NO USADO** de ancho 4, ocupa demasiado en 20x4!!!
#     NOTA podría ser de interés con un display de 40x4 ... ...
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
l22 =  "|  | | /  \ /   \/   \ /   /                     "
l23 =  "|__| |/   \X/   /\    |   /_                     "
l24 =  "                                                 "
#       1234 1234 1234 1234 1234 1234 1234 1234 1234 1234
l31 =  " _         _    _         __        __   _    _  "
l32 =  "| |   /|   _|   _)  |_|  |_     /    /  (_)  (_) "
l33 =  "|_|    |  (_    _)    |  __)   (_)  /   (_)   /  "
l34 =  "                                                 "

# USADO: ANCHO 3 es más difíl de representar pero es preferible
# ya que caben más caracteres en una pantalla LCD de ancho 20
#       123 123 123 123 123 123 123 123 123 123
f01 =  " _       _   _   _   __  _             "
f02 =  "|_| |_  /   | | |_  |_  |   |_|  |    |"
f03 =  "| | |_| |_  |_/ |_  |   |_] | |  |  |_|"
f04 =  "                                       "
#       123 123 123 123 123 123 123 123 123 123
f11 =  "                 _   _   _   _   _  ___"
f12 =  "|_/ |   |^| |/| | | |_) |_| |_) (_   | "
f13 =  "| | |__ | | | | |_| |     | ||   _)  | "
f14 =  "                                       "
#       123 123 123 123 123 123 123 123 123 123
f21 =  "                    __                 "
f22 =  "| | | / | / |/  |_/  /           .   . "
f23 =  "|_| |/  |X/ /|   |  /_   ,   .   ,   . "
f24 =  "                                       "
#       123 123 123 123 123 123 123 123 123 123
f31 =  " _       _   _       _      __   _   _ "
f32 =  "| |  /|  _|  _) |_| |_   /   /  (_) (_)"
f33 =  "|_|   | (_   _)   | __) (_) /   (_)  / "
f34 =  "                                       "
#       123 123 123 123 123 123 123 123 123 123 123
f41 =  "                              _ _          "
f42 =  "         -   +   *   /   -   |   |         "
f43 =  "    ___                  -   |_ _|   (   ) "
f44 =  "                                           "

def wbig3(c):
    """ devuelve 4 cadenas de ancho 3 para pintar
        un widget de un caracter grande en el LCD
    """
    c = c.lower()

    mis1 = [",", ".", ";", ":"]
    mis2 = [" ", "_", "-", "+", "*", "/", "=", "[", "]", "(", ")"]

    # letras
    if   ord(c) in range(97,107):
        col = (ord(c) - 97) * 4
        c1 = f01[col:col+3]
        c2 = f02[col:col+3]
        c3 = f03[col:col+3]
        c4 = f04[col:col+3]
    elif ord(c) in range(107,117):
        col = (ord(c) - 107) * 4
        c1 = f11[col:col+3]
        c2 = f12[col:col+3]
        c3 = f13[col:col+3]
        c4 = f14[col:col+3]
    elif ord(c) in range(117,123):
        col = (ord(c) - 117) * 4
        c1 = f21[col:col+3]
        c2 = f22[col:col+3]
        c3 = f23[col:col+3]
        c4 = f24[col:col+3]
    # digitos
    elif ord(c) in range(48,58):
        col = (ord(c) - 48) * 4
        c1 = f31[col:col+3]
        c2 = f32[col:col+3]
        c3 = f33[col:col+3]
        c4 = f34[col:col+3]
    # simbolos
    elif c in mis1:
        col = (mis1.index(c) + 6) * 4
        c1 = f21[col:col+3]
        c2 = f22[col:col+3]
        c3 = f23[col:col+3]
        c4 = f24[col:col+3]
    elif c in mis2:
        col = mis2.index(c) * 4
        c1 = f41[col:col+3]
        c2 = f42[col:col+3]
        c3 = f43[col:col+3]
        c4 = f44[col:col+3]

    else:
        c1=c2=c3=c4=""

    return c1,c2,c3,c4

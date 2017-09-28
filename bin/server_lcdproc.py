#!/usr/bin/env python
# -*- coding: utf-8 -*-
# from __future__ import with_statement # This isn't required in Python 2.6

# v2.0
# - Se revisa el codigo y se renombran funciones para legibilidad
#   decode_data -->     show_status
#   set_data    -->     show_widget
#
# - Se separa en una función la screen adicional para mostrar info
#
# - Distinos esquemas de presentación del status de FIRtro
#   que se pueden seleccionar en audio/config. De momento  hay dos ...
#   Se pueden consultar los esquemas con "server_lcdproc.py -h"
#   como se indica en audio/config. Es codigo hardwired pero algo es algo...

# v2.0a
# - Si audio/config lcd_info_timeout=0 no se presenta 
#   la pantalla efímera del comando ejecutado
# - Permite ajustar la prioridad de la pantalla principal de estado scr_1 

# Acceso a variables de FIRtro para configurar el LCD
import getconfig
from sys import argv as sys_argv

# http://lcdproc.sourceforge.net/docs/current-dev.html
import socket
import re
import time
import json
lcdproc_host = 'localhost'
lcdproc_port = 13666
# eights of a second
info_timeout = 8 * getconfig.lcd_info_timeout
lcdproc_socket = None

def split_by_n( seq, n ):
    # A generator to divide a sequence into chunks of n units
    while seq:
        yield seq[:n]
        seq = seq[n:]

def lcd_cmd(lcdproc_cmd):
    lcdproc_socket.send(lcdproc_cmd + '\n')
    lcdproc_out = lcdproc_socket.recv(1024).strip('\n')
    #lcdproc_out = lcdproc_out.strip('\n')
    return(lcdproc_out)

def lcd_cmd_s(lcdproc_cmd):
    # solo envía el comando es más rápido
    lcdproc_socket.send(lcdproc_cmd + '\n')

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
        return -1
    # Devuelve un chorizo
    lcdproc_version = lcd_cmd('hello')
    # Se extrae el alto y ancho del display
    lcd_hgt = int(re.sub(' .*', '', re.sub('.* hgt ', '', lcdproc_version)))
    lcd_wid = int(re.sub(' .*', '', re.sub('.* wid ', '', lcdproc_version)))
    # Registramos el nombre del cliente
    lcd_cmd_s('client_set name ' + client_name)
    # Devolvemos el tamaño del display
    return lcd_hgt, lcd_wid

def lcd_close():
    #lcd_cmd('screen_del ' + screen_id)
    lcdproc_socket.close()

def posi(coord):
    # auxiliar para colocar los widgets, usada por show_widgets
    # notese que se devuelve "columna  fila"
    return " ".join(str(x) for x in coord[::-1])

def printa_layouts():
    # ABAJO se deben  configurar estos  esquemas de presentacion
    print
    print " ----- ESQUEMA 1 (por defecto) ----"
    print "    12345678901234567890"
    print " 1  Vol: -12.5 HR: 22.0 "
    print " 2  Bass: -2 Treble: -3 "
    print " 3  input: analog       "
    print " 4  Loud: 12 (6.47 dB)  "
    print
    print " ----- ESQUEMA 2 ------------------"
    print "    12345678901234567890"
    print " 1  V -32.0 H 34.0  B -2"
    print " 2  B -2 T -3 sEQ DRC PQ"
    print " 3  input         Lns ST"
    print " 4  preset            mp"
    print

def show_widget(type, value):
    
    # Usamos nombres de tres letras para identificar los widgets aquí
    # al objeto de ayudar en las lineas de lanzamiento de widgets de más abajo
    #
    # Hay dos propiedades que definir:
    #   1 - Las coordenadas del widget, ejemplo       Cvol=1,1
    #       Nota: para que NO SE MUESTRE pondremos    Cvol=0,0
    #       OjO:  cuidado de no solapar widgets en la misma linea
    #
    #   2 - La etiqueta antes de mostrar el value del widget
    #       Ejemplo   Lvol = "Vol: "
    #
    # Puede ser necesario transformar values como se hace en el esquema 2

    # Inicializamos coordenadas y etiquetas a cero:
    Cvol=0,0; Chea=0,0; Cbal=0,0; Cbas=0,0; Ctre=0,0; Cseq=0,0; Cdrc=0,0;
    Cpeq=0,0; Cinp=0,0; Clns=0,0; Cmon=0,0; Cpre=0,0; Cfty=0,0; Clni=0,0;
    Lvol="";  Lhea="";  Lbal="";  Lbas="";  Ltre="";  Lseq="";  Ldrc="";
    Lpeq="";  Linp="";  Llns="";  Lmon="";  Lpre="";  Lfty="";  Llni="";

    # ---------- ESQUEMA 2 ------------
    if getconfig.lcd_layout == "2":

        # coordenadas
        Cvol=1,1;       Chea=1,9;                     Cbal=1,17;
        Cbas=2,1;  Ctre=2,6;  Cseq=2,11;  Cdrc=2,15;  Cpeq=2,19;
        Cinp=3,1;                         Clns=3,15;  Cmon=3,19;
        Cpre=4,1;                                     Cfty=4,19;

        # etiquetas para algunos values:
        Lvol="V ";     Lhea="H ";                 Lbal="B "
        Lbas="B ";   Ltre="T ";

        # Transformaciones de algunos values ya que en este esquema
        # los mostraremos solo si están activos
        if type == 'loud':
            if value == "True": value = "LNS"
            else:               value = " - "
        if type == 'syseq':
            if value == "True": value = "sEQ"
            else:               value = " - "
        if type == 'drc':
            if value<>"0":      value = "DRC"
            else:               value = " - "
        if type == 'peq':
            if value=="off":    value = "- "
            else:               value = "PQ"
        if type == 'mono':
            if value=="off":    value = "ST"
            else:               value = "MO"

    # ------- ESQUEMA 1 (POR DEFECTO) ------------
    else:

        # coordenadas
        Cvol=1,1;            Chea=1,12;
        Cbas=2,1;         Ctre=2,10;
        Cinp=3,1;
        Clni=4,1; # loudness_level_info de server_process

        # etiquetas para el value:
        Lvol="Vol: ";     Lhea="HR: "
        Lbas="Bass: ";   Ltre="Treb: ";
        Linp="Input: ";
        Llni="Loud: "
        
        # nota: este esquema no requiere transformaciones

    # Lanzamiento de los comandos para mostrar los widgets.
    # Recordatorio: los widgets DEBEN ESTAR DECLARADOS en lcd_configure_main_screen()
    if type == 'level':
        lcd_cmd_s('widget_set scr_1 level       ' + posi(Cvol) + ' "' + Lvol + value + '"')
    elif type == 'headroom':
        lcd_cmd_s('widget_set scr_1 headroom    ' + posi(Chea) + ' "' + Lhea + value + '"')
    elif type == 'balance':
        lcd_cmd_s('widget_set scr_1 balance     ' + posi(Cbal) + ' "' + Lbal + value + '"')

    elif type == 'bass':
        lcd_cmd_s('widget_set scr_1 bass        ' + posi(Cbas) + ' "' + Lbas + value + '"')
    elif type == 'treble':
        lcd_cmd_s('widget_set scr_1 treble      ' + posi(Ctre) + ' "' + Ltre + value + '"')
    elif type == 'syseq':
        lcd_cmd_s('widget_set scr_1 syseq       ' + posi(Cseq) + ' "' + Lseq + value + '"')
    elif type == 'drc':
        lcd_cmd_s('widget_set scr_1 drc         ' + posi(Cdrc) + ' "' + Ldrc + value + '"')
    elif type == 'peq':
        lcd_cmd_s('widget_set scr_1 peq         ' + posi(Cpeq) + ' "' + Lpeq + value + '"')

    elif type == 'input':
        lcd_cmd_s('widget_set scr_1 input       ' + posi(Cinp) + ' "' + Linp + value + '"')
    elif type == 'loud':
        lcd_cmd_s('widget_set scr_1 loud        ' + posi(Clns) + ' "' + Llns + value + '"')
    elif type == 'mono':
        lcd_cmd_s('widget_set scr_1 mono        ' + posi(Cmon) + ' "' + Lmon + value + '"')

    elif type == 'loudinfo':
        lcd_cmd_s('widget_set scr_1 loudinfo    ' + posi(Clni) + ' "' + Llni + value + '"')

    elif type == 'preset':
        lcd_cmd_s('widget_set scr_1 preset      ' + posi(Cpre) + ' "' + Lpre + value + '"')
    elif type == 'ftype':
        lcd_cmd_s('widget_set scr_1 ftype       ' + posi(Cfty) + ' "' + Lfty + value + '"')

    elif type == 'info' and info_timeout > 0:
        show_screenInfo(value)

    elif type == 'test':
        lcd_cmd_s('widget_set scr_1 volume 1 1 "   Test LCD FIRtro"')

def show_screenInfo(value):
    # Creamos una SCREEN ADICIONAL con informacion efímera (timeout)
    string = lcd_cmd('screen_add scr_info')
    lcd_cmd_s('screen_set scr_info priority foreground timeout ' + str(info_timeout))
    if string[:4] <> 'huh?': # huh? en el lenguaje lcdproc significa ¿comooooor?
        # La pantalla no existe, creamos los widgets
        lcd_cmd_s('widget_add scr_info info_tit title')
        lcd_cmd_s('widget_add scr_info info_txt2 string')
        lcd_cmd_s('widget_add scr_info info_txt3 string')
        lcd_cmd_s('widget_add scr_info info_txt4 string')
    lcd_cmd_s('widget_set scr_info info_tit "FIRtro info"')
    line = 2
    for data in split_by_n(value,20):
        lcd_cmd_s('widget_set scr_info info_txt' + str(line) + ' 1 ' + str(line) + ' "' + data + '"')
        line = line + 1
        if line == 5:
            break

def show_status(data, priority="info"):
    # Descofificamos los datos entregados que son json
    data = json.loads(data)
    #ver_tipos_json(data) # debug
    
    # permite redefinir la prioridad 'info' con la que se creó la pantalla principal de este módulo
    lcd_cmd_s('screen_set scr_1 priority '+ priority)

    # Visualizamos de los datos recibidos los que deseemos presentar en el LCD
    # NOTA: Los widgets a visualizar DEBEN ESTAR DECLARADOS 'widget_add'
    #       en lcd_configure_main_screen(), de tipo 'string'.
    show_widget('preset',      data['preset'])
    show_widget('ftype',       data['filter_type'])
    show_widget('input',       data['input_name'])
    show_widget('level',       str(data['level']))
    show_widget('bass',        str(int(data['bass'])))
    show_widget('treble',      str(int(data['treble'])))
    show_widget('balance',     str(int(data['balance'])).rjust(2))
    show_widget('headroom',    str(data['headroom']))
    show_widget('drc',         data['drc_eq'])
    show_widget('loud',        str(data['loudness_track']))
    show_widget('mono',        data['mono'])
    show_widget('syseq',       str(data['system_eq']))
    # caso especial tener en cuenta si peq está defeated
    if not data['peqdefeat']:
        show_widget('peq',         data['peq'])
    else:
        show_widget('peq',         "off")
    # caso especial loudness_level_info manipulado si loudness_track=False
    if data['loudness_track']:
        show_widget('loudinfo',    str(data['loudness_level_info']))
    else:
        show_widget('loudinfo',    "off")

    # Mostramos warnings o el comando recibido excepto si es 'status'
    if len(data['warnings']) > 0:
        show_widget('info', data['warnings'][0])
    elif data['order'] != 'status':
        show_widget('info', data['order'])

def lcd_configure_main_screen():
    # definimos la SCREEN principal de este módulo
    lcd_cmd_s('screen_add scr_1')
    # WIDGETS utilizables en la screen principal de este modulo
    lcd_cmd_s('widget_add scr_1 level       string')
    lcd_cmd_s('widget_add scr_1 headroom    string')
    lcd_cmd_s('widget_add scr_1 balance     string')
    lcd_cmd_s('widget_add scr_1 bass        string')
    lcd_cmd_s('widget_add scr_1 treble      string')
    lcd_cmd_s('widget_add scr_1 loud        string')
    lcd_cmd_s('widget_add scr_1 loudinfo    string')
    lcd_cmd_s('widget_add scr_1 input       string')
    lcd_cmd_s('widget_add scr_1 preset      string')
    lcd_cmd_s('widget_add scr_1 mono        string')
    lcd_cmd_s('widget_add scr_1 ftype       string')
    lcd_cmd_s('widget_add scr_1 syseq       string')
    lcd_cmd_s('widget_add scr_1 drc         string')
    lcd_cmd_s('widget_add scr_1 peq         string')

def test():
    lcd_size = init('FIRtro')
    if lcd_size == -1:
        return -1
    print '=> LCD ' + str(lcd_size[0])+' x ' +str(lcd_size[1])
    show_widget ('test', '')
    while True:
        string = raw_input('Mensaje emergente (quit para salir): ')
        if string == 'quit':
            break
        show_widget ('info', string)
    lcd_close()

def ver_tipos_json(data): # solo para debug
    for cosa in data:
        print ">"*5, cosa.ljust(12), type(data[cosa]), data[cosa]

def init(client_name):
    lcd_size = lcd_open(client_name)
    if lcd_size == -1:
        return -1
    lcd_configure_main_screen()
    return lcd_size

if __name__ == "__main__":
    if len(sys_argv) > 1:
        printa_layouts()
    else:
        test()

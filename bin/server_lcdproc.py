#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    Información de FIRtro en el LCD
    
    Para hacer pruebas en línea de comandos:

        server_lcdproc.py   --test          Inicia un modo interactivo para
                                            escribir mensajes en la pantalla LCD.

                            --level xx.xx   Se muestra el valor en números grandes.

                            --msg cadena    Se muestra la cadena en scroll con caracteres grandes.

                            --layouts       Se muestran las layouts predefinidas para
                                            presentar la pantalla resumen del estado de FIRtro.

    (Los mensajes de estas pruebas expiran en 10 seg)
"""

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
#
# v2.0a
# - Si audio/config lcd_info_timeout=0 no se presenta
#   la pantalla efímera informativa del comando solicitado
# - Permite ajustar la prioridad de la pantalla principal de estado scr_1
#
# v2.0b
# - Se separan las funciones básicas de interacción con el server LCDproc
#   en un módulo comun 'client_lcd.py', que se importa aquí.
#
# v3.0
#   - Se incorporan las facilidades de presentación del nivel en números grandes y
#     de scroll de mensajes en caracteres grandes.
# v3.0a
# - Se añade MUTE si mute=True en lcdbig.show_level()
# v3.0b
# - Disponible un scroll a pantalla completa que muestra una cadena de texto usando
#   las rutinas de lcdbig.py que escalan los caracteres mediante un artificio a base de
#   4 lineas de caracteres ascii básicos, ya que LCDproc no admite ascii extendido.
# v3.0c
# - Se separan las funiones básicas de interacción con el server LCDproc
#   en un módulo comun 'client_lcd.py', que se importa aquí.


from sys import argv as sys_argv
from time import sleep

# Módulo base para interactuar con un servidor LCDproc:
import client_lcd as cLCD

# Json es el formato del chorizo de estado que recibimos del server.py de FIRtro
import json

# Módulo auxiliar para escalar caracteres en 4 lineas
# y para mostrar dígitos grandes para la pantalla de level en grande:
import lcdbig

# Acceso a variables de FIRtro para configurar el LCD
import getconfig

def split_by_n( seq, n ):
    # A generator to divide a sequence into chunks of n units
    while seq:
        yield seq[:n]
        seq = seq[n:]

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
    print " 3  input_name    Lns ST"
    print " 4  preset_name       mp"
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
    # Recordatorio: los widgets DEBEN ESTAR DECLARADOS en _configure_main_screen()
    if type == 'level':
        cLCD.cmd_s('widget_set scr_1 level       ' + posi(Cvol) + ' "' + Lvol + value + '"')
    elif type == 'headroom':
        cLCD.cmd_s('widget_set scr_1 headroom    ' + posi(Chea) + ' "' + Lhea + value + '"')
    elif type == 'balance':
        cLCD.cmd_s('widget_set scr_1 balance     ' + posi(Cbal) + ' "' + Lbal + value + '"')

    elif type == 'bass':
        cLCD.cmd_s('widget_set scr_1 bass        ' + posi(Cbas) + ' "' + Lbas + value + '"')
    elif type == 'treble':
        cLCD.cmd_s('widget_set scr_1 treble      ' + posi(Ctre) + ' "' + Ltre + value + '"')
    elif type == 'syseq':
        cLCD.cmd_s('widget_set scr_1 syseq       ' + posi(Cseq) + ' "' + Lseq + value + '"')
    elif type == 'drc':
        cLCD.cmd_s('widget_set scr_1 drc         ' + posi(Cdrc) + ' "' + Ldrc + value + '"')
    elif type == 'peq':
        cLCD.cmd_s('widget_set scr_1 peq         ' + posi(Cpeq) + ' "' + Lpeq + value + '"')

    elif type == 'input':
        cLCD.cmd_s('widget_set scr_1 input       ' + posi(Cinp) + ' "' + Linp + value + '"')
    elif type == 'loud':
        cLCD.cmd_s('widget_set scr_1 loud        ' + posi(Clns) + ' "' + Llns + value + '"')
    elif type == 'mono':
        cLCD.cmd_s('widget_set scr_1 mono        ' + posi(Cmon) + ' "' + Lmon + value + '"')

    elif type == 'loudinfo':
        cLCD.cmd_s('widget_set scr_1 loudinfo    ' + posi(Clni) + ' "' + Llni + value + '"')

    elif type == 'preset':
        cLCD.cmd_s('widget_set scr_1 preset      ' + posi(Cpre) + ' "' + Lpre + value + '"')
    elif type == 'ftype':
        cLCD.cmd_s('widget_set scr_1 ftype       ' + posi(Cfty) + ' "' + Lfty + value + '"')

    elif type == 'info' and getconfig.lcd_info_timeout > 0:
        show_screen_Info(value)

    elif type == 'test':
        cLCD.cmd_s('widget_set scr_1 volume 1 1 "   Test LCD FIRtro"')

def show_screen_Info(value, to=getconfig.lcd_info_timeout):
    # Creamos una SCREEN ADICIONAL con informacion efímera (timeout)
    string = cLCD.cmd('screen_add scr_info')
    to = 8 * to # se debe indicar en 1/8sec al server
    cLCD.cmd_s('screen_set scr_info -cursor no -priority foreground -timeout ' + str(to))
    if string[:4] <> 'huh?': # huh? en el lenguaje lcdproc significa ¿comooooor?
        # La pantalla no existe, creamos los widgets
        cLCD.cmd_s('widget_add scr_info info_tit title')
        cLCD.cmd_s('widget_add scr_info info_txt2 string')
        cLCD.cmd_s('widget_add scr_info info_txt3 string')
        cLCD.cmd_s('widget_add scr_info info_txt4 string')
    cLCD.cmd_s('widget_set scr_info info_tit "FIRtro info"')
    line = 2
    for data in split_by_n(value,20):
        cLCD.cmd_s('widget_set scr_info info_txt' + str(line) + ' 1 ' + str(line) + ' "' + data + '"')
        line = line + 1
        if line == 5:
            break

def show_status(data, priority="info"):
    # Descofificamos los datos entregados que son json
    data = json.loads(data)
    #ver_tipos_json(data) # debug

    # permite redefinir la prioridad 'info' con la que se creó la pantalla principal de este módulo
    _configure_main_screen()

    # Visualizamos de los datos recibidos los que deseemos presentar en el LCD
    # NOTA: Los widgets a visualizar DEBEN ESTAR DECLARADOS 'widget_add'
    #       en _configure_main_screen(), de tipo 'string'.
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

def _configure_main_screen():
    # definimos la SCREEN principal de este módulo
    cLCD.cmd_s('screen_add scr_1')
    # WIDGETS utilizables en la screen principal de este modulo
    cLCD.cmd_s('widget_add scr_1 level       string')
    cLCD.cmd_s('widget_add scr_1 headroom    string')
    cLCD.cmd_s('widget_add scr_1 balance     string')
    cLCD.cmd_s('widget_add scr_1 bass        string')
    cLCD.cmd_s('widget_add scr_1 treble      string')
    cLCD.cmd_s('widget_add scr_1 loud        string')
    cLCD.cmd_s('widget_add scr_1 loudinfo    string')
    cLCD.cmd_s('widget_add scr_1 input       string')
    cLCD.cmd_s('widget_add scr_1 preset      string')
    cLCD.cmd_s('widget_add scr_1 mono        string')
    cLCD.cmd_s('widget_add scr_1 ftype       string')
    cLCD.cmd_s('widget_add scr_1 syseq       string')
    cLCD.cmd_s('widget_add scr_1 drc         string')
    cLCD.cmd_s('widget_add scr_1 peq         string')

def interactive_test_lcd():
    lcd_size = init('FIRtro')
    if lcd_size == -1:
        return -1
    print '=> LCD ' + str(lcd_size[0])+' x ' +str(lcd_size[1])
    show_widget ('test', '')
    while True:
        string = raw_input('Mensaje emergente (quit para salir): ')
        if string == 'quit':
            break
        show_widget('info', string)
    cLCD.close()

def ver_tipos_json(data): # solo para debug
    for cosa in data:
        print ">"*5, cosa.ljust(12), type(data[cosa]), data[cosa]

def init(client_name, server="localhost:13666"):
    if cLCD.open(client_name, server):
        return cLCD.get_size()
    else:
        return False
        
if __name__ == "__main__":

    # posibles opciones para pruebas desde la línea de comandos:
    # --test | --level cadena | -msg cadena | --layouts
    if len(sys_argv) > 1:
        opc = sys_argv[1]
        if len(sys_argv) > 2:
            cadena = sys_argv[2]

        init("tmp", server=getconfig.LCD_server)

        if "-t" in opc:
            interactive_test_lcd()

        elif opc == "--level":
            lcdbig.show_level(cadena, level_priority="foreground")
            sleep(10)

        elif opc == "--msg":
            lcdbig.show_scroller(cadena, priority="foreground")
            sleep(10)

        elif opc == "--layouts":
            printa_layouts()
            
        else:
            print __doc__

    # si no se pasan opciones por linea de comandos se muestra la ayuda:
    else:
        print __doc__

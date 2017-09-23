#!/usr/bin/env python
# -*- coding: utf-8 -*-
# from __future__ import with_statement # This isn't required in Python 2.6

# acceso a variables de FIRtro para configurar el LCD
import getconfig

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

def show_widget(type, value):

    # esquema:
    # 12345678901234567890
    # V -32.0 H 34.0  B -2
    # B -2 T -3 sEQ DRC PQ
    # entrada       Lns ST
    # preset            mp
    #                                          COL ROW
    if type == 'level':
        lcd_cmd_s('widget_set scr_1 level       1   1   "V ' + value + '"')
    elif type == 'headroom':
        lcd_cmd_s('widget_set scr_1 headroom    9   1   "H ' + value + '"')
    elif type == 'balance':
        lcd_cmd_s('widget_set scr_1 balance     17  1   "B ' + value + '"')

    elif type == 'bass':
        lcd_cmd_s('widget_set scr_1 bass        1   2   "B ' + value + '"')
    elif type == 'treble':
        lcd_cmd_s('widget_set scr_1 treble      6   2   "T ' + value + '"')
    elif type == 'syseq':
        lcd_cmd_s('widget_set scr_1 syseq       11  2   "' + value + '"')
    elif type == 'drc':
        lcd_cmd_s('widget_set scr_1 drc         15  2   "' + value + '"')
    elif type == 'peq':
        lcd_cmd_s('widget_set scr_1 peq         19  2   "' + value + '"')

    elif type == 'input':
        lcd_cmd_s('widget_set scr_1 input       1   3   "' + value + '"')
    elif type == 'loud':
        lcd_cmd_s('widget_set scr_1 loud        15  3   "' + value + '"')
    elif type == 'mono':
        lcd_cmd_s('widget_set scr_1 mono        19  3   "' + value + '"')

    elif type == 'preset':
        lcd_cmd_s('widget_set scr_1 preset      1   4   "' + value + '"')
    elif type == 'ftype':
        lcd_cmd_s('widget_set scr_1 ftype      19   4   "' + value + '"')

    elif type == 'info':
        # Creamos una SCREEN ADICIONAL con informacion (efímera)
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

    elif type == 'test':
        lcd_cmd_s('widget_set scr_1 volume 1 1 "   Test LCD FIRtro"')

def show_status(data):
    # Descofificamos los datos entregados que son json
    data = json.loads(data)
    #ver_tipos_json(data) # debug

    # Visualizamos cada uno de los datos recibidos
    show_widget('preset',      data['preset'])
    show_widget('ftype',       data['filter_type'])
    show_widget('input',       data['input_name'])
    show_widget('level',       str(data['level']))
    show_widget('bass',        str(int(data['bass'])))
    show_widget('treble',      str(int(data['treble'])))
    show_widget('balance',     str(int(data['balance'])).rjust(2))
    show_widget('headroom',    str(data['headroom']))
    # adaptamos loudness (boolean):
    if data['loudness_track'] == True:
        show_widget('loud', "Lns") # data['loudness_level_info']
    else:
        show_widget('loud', "   ")
    # adaptamos mono (unicode):
    if data['mono'] == "on":
        show_widget('mono', "MO")
    else:
        show_widget('mono', "ST")
    # adaptamos system_eq (boolean)
    if data['system_eq'] == True:
        show_widget('syseq', "sEQ")
    else:
        show_widget('syseq', "   ")
    # adaptamos drc_eq (unicode)
    if data['drc_eq'] <> "0":
        show_widget('drc', "DRC")
    else:
        show_widget('drc', "   ")
    # adaptamos peq (unicode)
    if data['peq'] <> "off" and data['peqdefeat'] == False:
        show_widget('peq', "PQ")
    else:
        show_widget('peq', "  ")

    # Mostramos warnings o el comando recibido excepto si es 'status'
    if len(data['warnings']) > 0:
        show_widget('info', data['warnings'][0])
    elif data['order'] != 'status':
        show_widget('info', data['order'])

def lcd_configure():
    # Widgets utilizables en la screen principal de este modulo
    lcd_cmd_s('screen_add scr_1')
    lcd_cmd_s('widget_add scr_1 level       string')
    lcd_cmd_s('widget_add scr_1 headroom    string')
    lcd_cmd_s('widget_add scr_1 balance     string')
    lcd_cmd_s('widget_add scr_1 bass        string')
    lcd_cmd_s('widget_add scr_1 treble      string')
    lcd_cmd_s('widget_add scr_1 loud        string')
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
    lcd_configure()
    return lcd_size

if __name__ == "__main__":
    test()

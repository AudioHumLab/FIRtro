#!/usr/bin/env python
# -*- coding: utf-8 -*-
# from __future__ import with_statement # This isn't required in Python 2.6

# http://lcdproc.sourceforge.net/docs/current-dev.html
import socket
import re
import time
import json
lcdproc_host = 'localhost'
lcdproc_port = 13666
# Value in eights of a second
info_timeout = 40
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
    return(lcd_hgt, lcd_wid)

def lcd_close():
    #lcd_cmd('screen_del ' + screen_id)
    lcdproc_socket.close()

def lcd_configure():
    # Creamos la(s) páginas
    # SCREEN_1
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

def init(client_name):
    lcd_size = lcd_open(client_name)
    if (lcd_size == -1): return -1
    lcd_configure()
    return lcd_size

def set_data (type, value):
                                            #   COL ROW
    if (type == 'level'):
        lcd_cmd_s('widget_set scr_1 level       1   1   "V ' + value + '"')

    elif (type == 'headroom'):
        lcd_cmd_s('widget_set scr_1 headroom    9   1   "Hr ' + value + '"')

    elif (type == 'balance'):
        lcd_cmd_s('widget_set scr_1 balance     17  1   "B ' + value + '"')

    elif (type == 'bass'):
        lcd_cmd_s('widget_set scr_1 bass        1   2   "Bas ' + value + '"')

    elif (type == 'treble'):
        lcd_cmd_s('widget_set scr_1 treble      9   2   "Tre ' + value + '"')

    elif (type == 'mono'):
        lcd_cmd_s('widget_set scr_1 mono        19  2   "' + value + '"')

    elif (type == 'input'):
        lcd_cmd_s('widget_set scr_1 input       1   3   "' + value + '"')

    elif (type == 'loud'):
        lcd_cmd_s('widget_set scr_1 loud        15  3   "Ld:' + value + '"')

    elif (type == 'preset'):
        lcd_cmd_s('widget_set scr_1 preset      1   4   "' + value + '"')

    elif (type == 'ftype'):
        lcd_cmd_s('widget_set scr_1 ftype      19 4 "' + value + '"')

    elif (type == 'info'):
        # Creamos una pantalla de informacion
        string=lcd_cmd('screen_add scr_info')
        lcd_cmd_s('screen_set scr_info priority foreground timeout ' + str(info_timeout))
        if (string[:4] <> 'huh?'):
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
            if (line == 5):
                break

    elif (type == 'test'):
        lcd_cmd_s('widget_set scr_1 volume 1 1 "   Test LCD FIRtro"')

def decode_data (data):
    # Descofificamos los datos para presentarlos en la pantalla
    data=json.loads(data)
    set_data('preset',      data['preset'])
    set_data('ftype',       data['filter_type'])
    set_data('input',       data['input_name'])
    set_data('level',       str(data['level']))
    set_data('bass',        str(int(data['bass'])))
    set_data('treble',      str(int(data['treble'])))
    set_data('balance',     str(int(data['balance'])))
    set_data('headroom',    str(data['headroom']))
    # adaptamos loudness:
    if data['loudness_track'] == True:
        set_data('loud', " ON") # data['loudness_level_info']
    else:
        set_data('loud', "OFF")
    # adaptamos mono/stereo:
    if data['mono'] == "on":
        set_data('mono', "MO")
    else:
        set_data('mono', "ST")

    # Mostramos el comando recibido, excepto si es un 'status'
    if (len(data['warnings']) > 0):
        set_data('info', data['warnings'][0])
    elif (data['order'] != 'status'):
        set_data('info', data['order'])

def test():
    lcd_size = init('FIRtro')
    if (lcd_size == -1):
        return -1
    print '=> LCD ' + str(lcd_size[0])+' x ' +str(lcd_size[1])
    set_data ('test', '')
    while True:
        string = raw_input('Mensaje emergente (quit para salir): ')
        if (string == 'quit'):
            break
        set_data ('info', string)
    lcd_close()

if __name__ == "__main__":
    test()

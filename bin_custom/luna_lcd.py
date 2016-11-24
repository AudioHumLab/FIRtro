#!/usr/bin/env python
#coding=utf-8

import socket
import re
import time

lcdproc_host = 'localhost'
lcdproc_port = 13666
info_timeout = 40 # Value in eights of a second
lcdproc_socket = None

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

# conectamos con el servidor
lcd_open("CLI_lunas")

# definimos la luna 'base' a trozos:
trozos = []
trozos.append("\ \*")
trozos.append("\*  ")
trozos.append("\*  ")
trozos.append("\ \*")

# definimos las 20 pantallas (de la SCR_0 a la SCR_19)
for pos in range(0,20):

    SCRid = "SCR_" + str(pos)
    lcd_cmd("screen_add " + SCRid)
    lcd_cmd("screen_set " + SCRid + " -priority hidden")

    # definimos las 4 lineas que componen la luna (widgets tipo string)
    for lin in range(0,4):
        WGid = "WG_" + str(lin+1)
        lcd_cmd("widget_add " + SCRid + " " + WGid + " string")
        WGdata = str(pos+1) + " " + str(lin +1) + " " + trozos[lin]
        lcd_cmd("widget_set " + SCRid + " " + WGid + " "+  WGdata)

delay = 1.5

while True:
    time.sleep(delay * 3)
    lcd_cmd("screen_set SCR_0 -priority alert")
    time.sleep(delay)
    for pos in range(0,20):
        SCRcurr = "SCR_" + str(pos)
        lcd_cmd("screen_set " + SCRcurr + " -priority hidden")
        if pos < 19:
            SCRnext = "SCR_" + str(pos+1)
            lcd_cmd("screen_set " + SCRnext + " -priority alert")
        time.sleep(delay)
    
lcd_close()





#!/usr/bin/env python
#coding=utf-8
# from __future__ import with_statement # This isn't required in Python 2.6

# v1.0b:
# se printa un separador en caso de control_clear=False en audio/config

import socket
import sys
import time
import os
import server_process
import server_lcdproc as lcd
import getconfig as conf

#############################################################
# Programa principal par atender las peticiones de clientes #
#############################################################

# Creamos el socket
try:
    s=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
except socket.error, e:
    print "(server) Error creating socket: %s" % e
    sys.exit(-1)
# Usamos la opciÛn socket.SO_REUSEADDR. Esto es para evitar este error:
# socket.error: [Errno 98] Address already in use
# que se puede producir si reinciamos este script
# This is because the previous execution has left the socket in a 
# TIME_WAIT state, and cannot be immediately reused.
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

# Enlazamos la direccion y el puerto
try:
    s.bind((conf.control_address,conf.control_port))
except:
    print "(server) Error binding port", conf.control_port
    s.close()
    sys.exit(-1)

# Intentamos inicializar el lcd
if (conf.enable_lcd):
    lcd_size = lcd.init('FIRtro')
    if (lcd_size == -1):
        # No se ha podido conectar con lcdproc. Deshabilitamos su uso
        use_lcd = False
        print "(server) Warning: Can not connect to lcdproc. LCD is disabled"
    else:
        print '(server) LCD enabled: ' + str(lcd_size[0])+' x ' +str(lcd_size[1])
        use_lcd = True
else: use_lcd = False

# Bucle para procesar las conexiones
# Numero de conexiones que se mantienen en cola
backlog = 10
while True:
    # Escuchamos el puerto
    if (conf.control_output>1): print "(server) Listening on address", conf.control_address, "port",str(conf.control_port) + "..." 
    s.listen(backlog)
    # En este punto aceptamos la conexiÛn del cliente
    sc,addr=s.accept()
    
    # RS: creo que con el clear de abajo es suficiente (pte revisar)
    #if conf.control_clear:
    #    os.system('clear')

    #if control_output>1:
    #    print "(server) Conected to client",addr[0]

    #Bucle para procesar las ordenes de la conexiÛn
    while True:
        data=sc.recv(4096)
        if not data:
            #Si no hay nada en el buffer, es que el cliente se ha desconectado antes de tiempo
            #if control_output>1: print "(server) Client disconnected. Closing connection..."
            sc.close()
            break
        elif data.rstrip('\r\n') == "close":
            sc.send("OK")
            #if control_output>1:
            #    print "(server) Closing connection..."
            sc.close()
            break
        elif data.rstrip('\r\n') == "quit":
            sc.send("OK")
            if conf.control_output>1:
                print "(server) Closing connection..."
            if (use_lcd):
                lcd.lcd_close()
            sc.close()
            s.close()
            sys.exit(1)
        else:
            if conf.control_clear:
                os.system('clear')
            else:
                 print "(server) ========================================================"
            status=server_process.do(data)
            sc.send(status)
            if (use_lcd):
                lcd.decode_data(status)
            #if control_output>1 and control_clear:
            #    print "(server) Conected to client",addr[0]
            #time.sleep(0.05)
    time.sleep(0.05)

#!/usr/bin/env python
# -*- coding: utf-8 -*-

# v1.0b:
# - se printa un separador en caso de control_clear=False en audio/config
# - algunos cambios en la sintaxis (espacios, paréntesis, comentarios)

# v2.0 beta
# - Incorporación del socket con MPD, para control de volumen enlazado:
#     Se separa el código de creación del socket
# - también se separa el código de inicialización del LCD

# v2.0a beta
# - se añade el lcd_big

import socket
import sys
from time import sleep
import os
import server_process
import getconfig
import server_lcdproc as lcd
import server_lcd_big as lcd_big

def getsocket(host, port):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    except socket.error, e:
        print "(server) Error creating socket: %s" % e
        sys.exit(-1)

    # Usamos la opción socket.SO_REUSEADDR. Esto es para evitar este error:
    # socket.error: [Errno 98] Address already in use
    # que se puede producir si reinciamos este script
    # This is because the previous execution has left the socket in a
    # TIME_WAIT state, and cannot be immediately reused.
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # intentamos crear el socket tcp:
    try:
        s.bind((host, port))
    except:
        print "(server) Error binding port", port
        s.close()
        sys.exit(-1)
    # se devuelve el socket creado:
    return s

def lcd_check():
    # Intentamos inicializar el lcd
    if getconfig.enable_lcd:
        lcd_size = lcd.init('FIRtro')
        if lcd_size == -1:
            # No se ha podido conectar con lcdproc. Deshabilitamos su uso
            print "(server) Warning: Can not connect to lcdproc. LCD is disabled"
            return False
        else:
            # Añadimos el cliente LCD en numeros gordos
            lcd_big.crea_cliente()
            print '(server) LCD enabled: ' + str(lcd_size[0])+' x ' +str(lcd_size[1])
            return True
    else:
        return False

if __name__ == "__main__":

    # Uso del LCD
    use_lcd = lcd_check()

    fsocket = getsocket(getconfig.control_address, getconfig.control_port)

    # Bucle PRINCIPAL para procesar las posibles conexiones.
    backlog = 10    # Numero de conexiones que se mantienen en cola
    while True:

        # Escuchamos los puertos
        fsocket.listen(backlog)
        if getconfig.control_output > 1:
            print "(server) Listening on address", getconfig.control_address, "port",str(getconfig.control_port) + "..."

        # En este punto aceptamos la conexión del cliente
        sc, addr = fsocket.accept()

        # informativo si está habilitado el printado
        if getconfig.control_output > 1:
            if getconfig.control_clear:
                # opción de borrado del terminal
                os.system('clear')
            else:
                # opción de separador
                 print "=" * 70
            print "(server) Conected to client", addr[0]

        # Bucle buffer para procesar la orden recibida en la conexión
        while True:
            # RECEPCION
            data = sc.recv(4096)
            if not data:
                # Si no hay nada en el buffer, es que el cliente se ha desconectado antes de tiempo
                if getconfig.control_output > 1:
                    print "(server) Client disconnected. Closing connection..."
                sc.close()
                break
            elif data.rstrip('\r\n') == "close":
                sc.send("OK")
                if getconfig.control_output > 1:
                    print "(server) Closing connection..."
                sc.close()
                break
            elif data.rstrip('\r\n') == "quit":
                sc.send("OK")
                if getconfig.control_output > 1:
                    print "(server) Closing connection..."
                if use_lcd:
                    lcd.lcd_close()
                    lcd_big.lcd_close()
                sc.close()
                fsocket.close()
                sys.exit(1)
            else:
                # SE HA RECIBIDO UNA ORDEN en 'data',
                # ENVIAMOS la orden al gestor de FIRtro (server_process.py)
                # que nos responde con el estado)
                status = server_process.do(data)

                # DEVOLVEMOS el estado de FIRtro
                sc.send(status)

                if use_lcd:
                    # pantalla general del lcd
                    lcd.show_status(status)
                    # nuevo cliene lcd que muestra el level con numeros grandes:
                    tmp = status[status.index('"level":'):]
                    tmp = tmp.split(",")[0].split()[-1]
                    lcd_big.show_level(tmp)

                if getconfig. control_output > 1 and getconfig.control_clear:
                    print "(server) Conected to client", addr[0]

        sleep(0.05)


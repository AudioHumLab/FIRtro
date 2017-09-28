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
            print "(server) Warning: Can not connect to lcdproc. LCD_STATUS is disabled"
            return False
        else:
            print '(server) LCD_STATUS enabled: ' + str(lcd_size[0])+' x ' +str(lcd_size[1])
            return True
    else:
        print '(server) LCD_STATUS disabled'
        return False

def lcd_big_check():
    # Intentamos inicializar el lcd
    if getconfig.enable_lcd_big:
        lcd_size = lcd_big.crea_cliente("BIGLEVEL")
        if lcd_size:
            print '(server) LCD_BIG enabled: ' + str(lcd_size[0])+' x ' +str(lcd_size[1])
            return True
        else:
            print "(server) Warning: Can not connect to lcdproc. LCD_BIG is disabled"
            return False
    else:
        print '(server) LCD_BIG disabled'
        return False

def _extrae_statusJson(param):
    # auxiliar
    tmp = status[status.index('"' + param + '":'):]
    tmp = tmp.split(",")[0].split()[-1]
    if tmp == "false":  tmp = False
    elif tmp == "true": tmp = True
    return tmp

def _show_big_scroller(orden):
    # auxiliar

    # OjO algunos parámetros tienen nombre de orden distinto
    if "drc" in orden:
        param = "drc_eq"
    elif "syseq" in orden:
        param = system_eq
    elif "peq" in orden:
        param = "peq"
    elif "loudness" in orden:
        param = "loudness_track"
    else:
        param = orden

    estado = _extrae_statusJson(param)
    msgLCD = orden + ": " + estado
    lcd_big.show_big_scroller(msgLCD, \
                              priority="foreground", \
                              timeout=9)


if __name__ == "__main__":

    # Uso del LCD
    use_lcd =     lcd_check()
    use_lcd_big = lcd_big_check()

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
                if use_lcd_big:
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

                # LCD. NUEVAS pantallas que muestran caracteres GRANDES:
                if use_lcd_big:
                    orden = data.split()[0].split("_")[0]

                    # SCROLL. Si alguno de los items configurados en audio/bigscroll_items
                    # matchea en la orden, presentamos la orden en el scroller grande:
                    if [item for item in getconfig.bigscroll_items if item in orden]:
                        _show_big_scroller(orden)

                    # LEVEL. Además también rotamos el nivel en grande:
                    lev = _extrae_statusJson("level")
                    mut = _extrae_statusJson("muted")
                    lcd_big.show_level(lev, mut, mute_priority=getconfig.lcd_show_mute_prio)

                # LCD. Pantalla general del ESTADO de FIRtro
                if use_lcd:
                    lcd.show_status(status, priority="info")

                if getconfig. control_output > 1 and getconfig.control_clear:
                    print "(server) Conected to client", addr[0]

        sleep(0.05)


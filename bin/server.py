#!/usr/bin/env python
# -*- coding: utf-8 -*-

# v1.0b:
# - se printa un separador en caso de control_clear=False en audio/config
# - algunos cambios en la sintaxis (espacios, paréntesis, comentarios)

# v2.0 beta
# - Incorporación del socket con MPD, para control de volumen enlazado:
#     Se separa el código de creación del socket
# - también se separa el código de inicialización del LCD

# v2.0a
# - se añade el server_lcd_big

import socket
import sys
from time import sleep
import os
import server_process
import getconfig
import server_lcdproc as srv_lcd
import server_lcd_big as srv_lcd_big

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
    # Intentamos inicializar el cliente lcd original en el server LDCproc
    if getconfig.enable_lcd:
        lcd_size = srv_lcd.init('FIRtro', server=getconfig.LCD_server)
        if lcd_size:
            print '(server) LCD_STATUS enabled: ' + str(lcd_size[0])+' x ' +str(lcd_size[1])
            return True
        else:
            # No se ha podido conectar con lcdproc. Deshabilitamos su uso
            print "(server) Warning: Can not connect to lcdproc. LCD_STATUS is disabled"
            return False
    else:
        print '(server) LCD_STATUS disabled'
        return False

def lcd_big_check():
    # Intentamos inicializar el nuevo cliente lcd de caractreres grandes en el server LDCproc
    if getconfig.enable_lcd_big:
        lcd_size = srv_lcd_big.crea_cliente("BIGLEVEL", server=getconfig.LCD_server)
        if lcd_size:
            print '(server) LCD_BIG enabled: ' + str(lcd_size[0])+' x ' +str(lcd_size[1])
            return True
        else:
            print "(server) Warning: Can not connect to lcdproc. LCD_BIG is disabled"
            return False
    else:
        print '(server) LCD_BIG disabled'
        return False

def _extrae_statusJson(svar):
    # auxiliar para leer el estado de una variable en el chorizo Json 'status'
    tmp = status[ status.index('"' + svar + '":'): ]
    tmp = tmp.split(",")[0].split()[-1]
    if tmp == "false":  tmp = False
    elif tmp == "true": tmp = True
    return tmp

def _show_big_scroller(comando, statusJson):
    # Func auxiliar para presentar el estado de un 'item' de interés en el scroller lcd_big.

    # La cadena json 'statusJson' es recibida desde server_process.do(orden)
    
    # Adecuaciones:
    #  - Algunas variables de estado 'svar' tienen un nombre
    #    distinto al propio comando que las modifica.
    #  - Además alguna función como syseq está implementada con dos comandos diferentes.
    item =      comando
    if "drc" in comando:
        svar =      "drc_eq"
    elif "syseq" in comando:
        item =      "syseq"
        svar =      "system_eq"
    elif "peq_reload" in comando:
        svar =      "peq"
    elif "peq_defeat" in comando:
        svar =      "peqdefeat"
    elif "loudness" in comando:
        item =      "ludness"
        svar =      "loudness_track"
    else:
        svar =      comando

    # Buscamos el estado de la variable de interés
    estado = _extrae_statusJson(svar)

    # Lo adecuamos para presentarlo en pantalla
    if      estado == True:  estado = "ON"
    elif    estado == False: estado = "OFF"
    else:                    estado = str(estado)

    # Y finalmente lo presentamos
    msgLCD = item + ": " + estado
    srv_lcd_big.show_big_scroller(msgLCD, \
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

            # Si no hay nada en el buffer, es que el cliente se ha desconectado antes de tiempo
            if not data:
                if getconfig.control_output > 1:
                    print "(server) Client disconnected. Closing connection..."
                sc.close()
                break

            # Se pide cerrar la conexión con el script de control client.py (modo interactivo)
            elif data.rstrip('\r\n') == "close":
                sc.send("OK")
                if getconfig.control_output > 1:
                    print "(server) Closing connection..."
                sc.close()
                break

            # Se pide salir de este script y cerrar todo (modo interactivo)
            elif data.rstrip('\r\n') == "quit":
                sc.send("OK")
                if getconfig.control_output > 1:
                    print "(server) Closing connection..."
                if use_lcd:
                    srv_lcd.lcd.close()
                if use_lcd_big:
                    srv_lcd_big.lcd.close()
                sc.close()
                fsocket.close()
                sys.exit(1)

            # Modo tranparente hacia FIRtro: 'data' es una ORDEN  (comando parámetros...)
            else:
                # 1. ENVIAMOS la orden al gestor de FIRtro (server_process.py)
                # que nos responderá con el estado general en formato json
                orden = data
                status = server_process.do(orden)

                # DEVOLVEMOS el estado de FIRtro
                sc.send(status)

                # 2. LCD. NUEVAS pantallas que muestran caracteres GRANDES:
                if use_lcd_big:

                    # SCROLL. Si alguno de los items configurados en audio/bigscroll_items
                    # matchea en el comando, presentamos la orden en el scroller grande:
                    comando = orden.split()[0]
                    if [item for item in getconfig.bigscroll_items if item in comando]:
                        _show_big_scroller(comando, statusJson=status)

                    # LEVEL. Además también rotamos el nivel en grande:
                    lev = _extrae_statusJson("level")
                    mut = _extrae_statusJson("muted")
                    srv_lcd_big.show_level(lev, mut, mute_priority=getconfig.lcd_show_mute_prio, \
                                       duration=2)

                # 3. LCD. Pantalla general resumen del ESTADO de FIRtro:
                if use_lcd:
                    srv_lcd.show_status(status, priority="info")

                if getconfig. control_output > 1 and getconfig.control_clear:
                    print "(server) Conected to client", addr[0]

        sleep(0.05)

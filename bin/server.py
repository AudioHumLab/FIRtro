#!/usr/bin/env python
# -*- coding: utf-8 -*-

# v1.0b:
# - se printa un separador en caso de control_clear=False en audio/config
# - algunos cambios en la sintaxis (espacios, paréntesis, comentarios)
#
# v2.0 beta
# - Incorporación del socket con MPD, para control de volumen enlazado:
#     Se separa el código de creación del socket
# - También se separa el código de inicialización del LCD
#
# v2.0a
# - Se usan las nuevas las pantallas de LCD con caracteres grandes.
#
# v2.0b
# - Se añade la comunicación de eventos hacia el server_infofifo.py
#
# v3.0a
# - Se escuchan también posibles metadata de los players, que serán añadidos
#   a mayores en el Json del estado del audio que llega de server_process.do(orden)
#   y que se envía a la web de FIRtro que se conecta como cliente de este server.

import json
import socket
import sys
from time import sleep
import os
import server_process
import getconfig
import server_lcdproc as srvLCD
import client_infofifo as cFIFO

from ConfigParser import ConfigParser
radiopresets = ConfigParser()
radiopresets.read("/home/firtro/audio/radio")

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
    # Intentamos inicializar el cliente LCD
    if getconfig.enable_lcd:
        lcd_size = srvLCD.open('FIRtro', server=getconfig.LCD_server_addr)
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

def infofifo_check():
    # Intentamos inicializar el cliente FIFO
    if getconfig.load_INFOFIFO_server:
        if cFIFO.open():
            cFIFO.close()
            return True
    return False

def _extrae_statusJson(svar):
    # auxiliar para leer el estado de una variable en el chorizo Json 'status'
    tmp = json_status[ json_status.index('"' + svar + '":'): ]
    tmp = tmp.split(",")[0].split()[-1]
    if tmp == "false":  tmp = False
    elif tmp == "true": tmp = True
    return tmp

def _prepare_big_scroller(comando, statusJson):
    # Func auxiliar intermedia para presentar el estado
    # de un 'item' de interés en el scroller lcd_big.

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

    return item + ": " + estado

def _is_metadataJson(data):
    try:
        dicc = json.loads(data)
        if dicc['player'] in PLAYERS:
            return True
    except:
        pass
    return False

if __name__ == "__main__":

    PLAYERS = ["mpd", "spotify", "mplayer"]
    # Inicialización del diccionario completo (estado_de_FIRtro + metadatas_de_cada_PLAYER)
    # que enviaremos a la web.
    # NOTA: las keys de estado_de_FIRtro serán incorporadas en el arranque gracias
    #       a los comandos iniciales que provocan su generación en server_process.do()
    plantillameta = {'artist':'', 'album':'', 'title':'', 'state':''}
    dicci_status_players = {"mpd":      plantillameta,
                            "spotify":  plantillameta,
                            "mplayer":  plantillameta}

    # Uso del LCD
    use_lcd = lcd_check()
    # Uso de INFOFIFO
    use_infofifo = infofifo_check()

    # Iniciamos el socket de este server.py:
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
        # OjO este loop se romperá (break) en cada conexión, pasando al loop PRINCIPAL...
        while True:

            # RECEPCION
            data = sc.recv(6000)
            #data = ""
            #while True
            #    buff = sc.recv(1024)
            #    if buff == "":
            #        break
            #    data += buff

            # Si no hay nada en el buffer, es que el cliente se ha desconectado antes de tiempo
            if not data:
                if getconfig.control_output > 1:
                    print "(server) Client disconnected. Closing connection..."
                sc.close()
                break

            # Se pide cerrar la conexión con el script de control client.py (modo interactivo)
            #elif data.rstrip('\r\n') == "close":
            elif data.startswith("close"):
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
                    srvLCD.cLCD.close()
                sc.close()
                fsocket.close()
                sys.exit(1)

            # Llegan metadatos de un PLAYER
            elif _is_metadataJson(data):
                # Ejempo: {'player': mpd, 'metadata':{'artist':'Rosendo', 'album':...}}
                dicci_player = json.loads(data)
                # Lo incorporamos a mayores en el diccionario general 'dicci_status_players'
                dicci_status_players[dicci_player['player']] = dicci_player['metadata']
                # Y lo enviamos a la página web
                json_status_players = json.dumps(dicci_status_players)
                # print "OOOOOOOO", len(json_status_players), json_status_players # (DEBUG)
                sc.send(json_status_players)

                sc.close() # (!) IMPORTANTE no olvidar cerrar el cliente
                break

            # Llega una ORDEN para server_process.do(comando parámetros...)
            else:
                # 1. ENVIAMOS la orden al gestor de FIRtro (server_process.py)
                # que nos responderá con el estado general en formato json
                orden = data
                json_status = server_process.do(orden)
                # Actualizamos el diccionario general y le incorporamos los player
                # xxxxxxxx
                old = dicci_status_players
                dicci_status_players = json.loads(json_status)
                for player in PLAYERS:
                    dicci_status_players[player] = old[player]
                # xxxxxxxx

                # Incorporamos manualmente el nombre de la EMISORA en los metadatos
                radio = dicci_status_players["radio"]
                tmp = "canal: " + radio
                dicci_status_players["mplayer"]["artist"] = tmp
                tmp = radiopresets.get("channels", radio).replace("\\","")
                dicci_status_players["mplayer"]["album"] = tmp
                dicci_status_players["mplayer"]["state"] = "play"

                # 2. ENVIAMOS a los clientes (la web) el status de FIRtro
                #             y los metadata de los PLAYERS:
                json_status_players = json.dumps(dicci_status_players)
                # print "OOOOOOOO", len(json_status_players), json_status_players # (DEBUG)
                sc.send(json_status_players)

                # 3. Presentamos el estado en el LCD
                if use_lcd:

                    # 3.1 Pantalla general resumen del ESTADO de FIRtro:
                    srvLCD.show_status(json_status, priority="info")

                    # 3.2 NUEVAS pantallas que muestran caracteres GRANDES:

                    # 3.2.1 SCROLL. Si alguno de los items configurados en audio/config:lcd_bigscroll_items
                    # matchea en el comando, presentamos la orden en el scroller grande:
                    comando = orden.split()[0]
                    if [item for item in getconfig.lcd_bigscroll_items if item in comando]:
                        try:    # esto es por si el comando es erróneo (Wrong sintax)
                            msgLCD = _prepare_big_scroller(comando, statusJson=json_status)
                            srvLCD.lcdbig.show_scroller(msgLCD, priority="foreground", timeout=9)
                        except:
                            pass

                    # 3.2.2 LEVEL. Además también rotamos el nivel en grande:
                    lev = _extrae_statusJson("level")
                    mut = _extrae_statusJson("muted")
                    srvLCD.lcdbig.show_level(lev, mut, mute_priority=getconfig.lcd_show_mute_prio, \
                                       duration=2)

                # 4. Refrescamos la INFOFIFO
                if use_infofifo:
                    cFIFO.open()
                    # enviamos el diccionario json del estado de FIRtro,
                    # precedido por una etiqueta identificativa:
                    cFIFO.cmd_s("statusFIRtro" + json_status)
                    cFIFO.close()

                if getconfig. control_output > 1 and getconfig.control_clear:
                    print "(server) Conected to client", addr[0]

        sleep(0.05)

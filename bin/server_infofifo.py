#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    'server_infofifo.py'

    Servidor para escribir el ESTADO de FIRtro y/o
    los METADATOS del Player en curso.

    El formato de los datos recibidos debe ser una CADENA JSON,
    precedida por el nombre del remitente, ejemplo:

        Spotify {"artist":"Pink Floyd", "album":"Whis You ..., ...}

    La salida se guarda en una FIFO en forma de líneas imprimibles.

    La fifo podrá ser printada mediante el script 'printinfofifo.py',
    por ejemplo usando una tablet conectada por ssh a FIRtro.
"""
# v1.0

from sys import argv as sys_argv
import socket
from time import sleep, ctime
from status2fifo import jsonStatus2fifo
import json
from ConfigParser import ConfigParser

fname = "/home/firtro/info_fifo"
radiopresets = ConfigParser()
radiopresets.read("/home/firtro/audio/radio")


def getsocket(host, port):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    except socket.error, e:
        print "(server) Error creating socket: %s" % e
        raise SystemExit, 0

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
        raise SystemExit, 0
    # se devuelve el socket creado:
    return s

def jsonMetadata2fifo(d):
    m = json.loads(d)

    try: state =        m['state']
    except: state =     ""
    try: artist =       m['artist']
    except: artist =    "unknown artist"
    try: album =        m['album']
    except: album =     "unknown album"
    try: title =        m['title']
    except: title =     "unknown title"

    if "pause" in state:
        state="(PAUSED)"
    else:
        state=""

    meta2fifo = "\n".join( [artist + "    " + state, album, title] )

    # para evitar UnicodeEncodeError: 'ascii' codec can't encode character u'\xf3' al escribir en la fifo
    return meta2fifo.encode('utf-8')

def _infoPlayer(input_name):
    # auxiliar para seleccionar la variable info_XXX correspondiente a una entrada
    d = {   "analog":   info_Analog,
            "spotify":  info_Spotify,
            "mpd":      info_MPD,
            "tdt":      info_TDT,
            "tdt_mpa":  info_TDT,
            "tdt_a52":  info_TDT
        }
    if input_name in d:
         return d[input_name]
    else:
        return input_name.upper()

if __name__ == "__main__":

    if len(sys_argv) > 1 and "-h" in sys_argv[1]:
        print __doc__
        raise SystemExit , 0

    sAddress="localhost"
    sPort=9995

    fsocket = getsocket(sAddress, sPort)

    backlog = 2
    fsocket.listen(backlog)
    print "(server_infofifo) Listening on address", sAddress, "port",str(sPort) + "..."

    info_FIRtro     = "-"
    info_Spotify    = "SPOTIFY"
    info_Analog     = "ANALOG"
    info_MPD        = "MPD"
    info_TDT        = "TDT"
    input_name      = ""

    while True:

        # Esperamos la conexión de clientes
        conn, addr = fsocket.accept()
        #print "(server_infofifo) Conected to client", addr

        # Leemos el buffer recibido:
        data = ""
        while True:
            recv = conn.recv(4096)
            if not recv:
                break
            data += recv

        #Tomamos nota de los datos recibidos
        if "{" in data:
            sender = data.split("{")[0].strip()
            jdic =  "{" + data.split("{")[1]
        else:
            sender = ""
            jdic  = "{}"

        try:
            tmp = json.loads(jdic)
            input_name = tmp['input_name']
            radio =      tmp['radio']
            tmp = "TDT canal: " + radio + "\n" + radiopresets.get("channels", radio).replace("\\","")
            info_TDT = tmp
        except:
            pass

        if sender ==   "statusFIRtro":
            info_FIRtro =   jsonStatus2fifo(jdic)
        elif sender == "Spotify":
            info_Spotify =  jsonMetadata2fifo(jdic)
        elif sender == "MPD":
            info_MPD =      jsonMetadata2fifo(jdic)

        if data:
            ########################################
            # Construimos el contenido de la FIFO: #
            ########################################
            f = open(fname, "w")
            ## 1st: las líneas del ESTADO de FIRtro
            f.write( info_FIRtro + "\n" )
            ## 2nd: Las líneas de METADATA del PLAYER actual
            f.write( _infoPlayer(input_name) )
            f.close()

        #print "(server_infofifo) closing client", addr  # DEBUG
        conn.close()

        sleep(0.1)

#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
    Script daemon que atiende eventos de MPD y los comunica a los server de display
"""

# v1.0

from mpd import MPDClient
import json
from sys import argv as sys_argv
from time import sleep

# clientes para interactuar con los servidores de DISPLAYs de FIRtro
import client_lcd as cLCD
import client_infofifo as cFIFO
import getconfig

def input_name():
    # función auxiliar para conocer el nombre de la entrada actual
    try:
        tmp = check_output('grep "input =" /home/firtro/audio/status', shell=True)
        return tmp.split()[-1]
    except:
        return ""

def do_mpd_LCDscreen(artistAlbumTitle, speed=3):
    # aux para printar los 3 elementos de artistAlbumTitle en el LCD
    artist, album, title = artistAlbumTitle
    speed = str(speed)
    # creamos la pantalla
    cLCD.create_screen("mpd_scr1", duration=10)
    # comandos para la linea 1: widget de título
    w1_add = "widget_add mpd_scr1 w1 title"
    w1_set = "widget_set mpd_scr1 w1 \ \ \ \ \ MPD\ \ \ \ \ \ "
    # comandos para las lineass 2-4: widgets del artista, album y pista
    w2_add = "widget_add mpd_scr1 w2 scroller"
    w3_add = "widget_add mpd_scr1 w3 scroller"
    w4_add = "widget_add mpd_scr1 w4 scroller"
    w2_set = "widget_set mpd_scr1 w2 1 2 20 2 m " + speed + " " + artist.replace(" ", "\ ")
    w3_set = "widget_set mpd_scr1 w3 1 3 20 3 m " + speed + " " + album.replace(" ", "\ ")
    w4_set = "widget_set mpd_scr1 w4 1 4 20 4 m " + speed + " " + title.replace(" ", "\ ")
    # lanzamiento de comandos al server LCDd
    cLCD.cmd_s(w1_add)
    cLCD.cmd_s(w2_add)
    cLCD.cmd_s(w3_add)
    cLCD.cmd_s(w4_add)
    cLCD.cmd_s(w1_set)
    cLCD.cmd_s(w2_set)
    cLCD.cmd_s(w3_set)
    cLCD.cmd_s(w4_set)

def do_static_LCDscreen():
    # aux para printar una pantalla estática indicando que 
    # la sesion no disppne de conexión con MPD
    # Creamos la pantalla
    cLCD.create_screen("static", duration=0)
    # Comandos para la linea 1: widget de título
    w1_add = "widget_add static w1 title"
    w1_set = "widget_set static w1 SIN\ CONEXION\ MPD"
    cLCD.cmd_s(w1_add)
    cLCD.cmd_s(w1_set)

def do_mpd_INFOFIFOscreen(artistAlbumTitle, paused=False):
    # aux para printar los 3 elementos de artistAlbumTitle en la INFOFIFO
    artist, album, title = artistAlbumTitle
    if paused: state = "pause"
    else:      state = "play" 
    d = {'artist':artist, 'album':album, 'title':title, 'state':state}
    jsonMetadata = json.dumps(d)
    # Info al server_infofifo en formato JSON con etiqueta previa:
    cFIFO.open()
    cFIFO.cmd_s( "MPD " + jsonMetadata)
    cFIFO.close()

def do_static_INFOFIFOscreen():
    # aux para printar una pantalla estática indicando que 
    # la sesion no disppne de conexión con MPD
    artist = 'NOT connected to MPD'
    d = {'artist':artist}
    jsonMetadata = json.dumps(d)
    cFIFO.open()
    cFIFO.cmd_s( "MPD " + jsonMetadata)
    cFIFO.close()

def on_metadata(artistAlbumTitle):
    """ Handler para cuando ocurre UN CAMBIO DE METADATA """
    if use_lcd:
        do_mpd_LCDscreen(artistAlbumTitle, speed=2)
    if use_infofifo:
        do_mpd_INFOFIFOscreen(artistAlbumTitle, paused=False)

def on_play(player):
    """ Handler para cuando se INICIA la reproducción """
    if use_lcd:
        # Restaura el título de la screen de Spotify quitando el indicador PAUSED
        cLCD.cmd_s("widget_set mpd_scr1 w1 \ \ \ Spotify\ \ \ \ ")
    if "spotify" in input_name().lower():
        if use_lcd:
            # recupera la prioridad normal de la screen LCD de Spotify
            cLCD.cmd_s("screen_set mpd_scr1 -priority info")
        if use_infofifo:
            # printa metadata en INFOFIFO
            do_mpd_INFOFIFOscreen(artistAlbumTitle, paused=False)

def on_pause(player):
    """ Handler para cuando se PAUSA """
    if use_lcd:
        # Modifica el título de la screen LCD de Spotify añadendo el indicador PAUSED
        cLCD.cmd_s("widget_set mpd_scr1 w1 Spotify\ PAUSED")
        if not "spotify" in input_name().lower():
            # opc.A borra la screen de Spotify
            #cLCD.delete_screen("mpd_scr1")
            # opc.B deja la screen de Spotify en background
            cLCD.cmd_s("screen_set mpd_scr1 -priority background")
    if use_infofifo:
        do_mpd_INFOFIFOscreen(artistAlbumTitle, paused=True)

def try_INFOFIFO_server():
    i = 0
    while i < 5:
        if not cFIFO.open():
            sleep(.2); cFIFO.close()
            print "(mpdmonitor) ERROR conectando con el server FIFO"
        else:
            sleep(.2); cFIFO.close()
            print "(mpdmonitor) conectado al server FIFO"
            return True
        sleep(1)
        i += 1
    return False

def try_LCD_server(server):
    #
    # (!) IMPORTANTE: aquí no hacemos close ya que mantenemos la conexión
    #                 con el LCDd para ir cambiando las pantallas
    i = 0
    while i < 5:
        if cLCD.open("mpd_client", server):
            print "(mpdmonitor) conectado al server LCDd"
            return True
        sleep(1)
        i += 1
    cLCD.close()
    print "(mpdmonitor) ERROR conectando con el server LCDd"
    return False

if __name__ == "__main__":

    if len(sys_argv) > 1:
        print __doc__
        raise SystemExit, 0

    use_infofifo = try_INFOFIFO_server()
    use_lcd =      try_LCD_server(getconfig.LCD_server_addr)

    # Intenta conexión con MPD
    mpdcli = MPDClient()
    try:
        mpdcli.connect("localhost", 6600)
        print "(mpdmonitor) conectado con MPD"
    except:
        if use_lcd:      do_static_LCDscreen()
        if use_infofifo: do_static_INFOFIFOscreen()
        print "(mpdmonitor) ERROR conectando con MPD"
        raise SystemExit, 0

    # BUCLE PRINCIPAL
    while True:
        # https://pythonhosted.org/python-mpd2/topics/commands.html
        #'MPDClient.idle(sub1, ...)' waits for a MPD change on the indicated subsystems ...
        # ... when something happens, idle ends, then this script continues.
        try:
            mpdcli.idle('player', 'message', 'playlist')
        except:
            print "(mpdmonitor) Terminado. se ha perdido la conexión con MPD."
            raise SystemExit, 0

        try:
            artist =    mpdcli.currentsong()['artist']
            album =     mpdcli.currentsong()['album']
            title =     mpdcli.currentsong()['title']
        except: # posiblemente la playlist está vacía
            artist = "--"
            album =  "--"
            title =  "--"

        artistAlbumTitle = artist, album, title
        # print artistAlbumTitle # DEBUG

        state =     mpdcli.status()['state']

        do_mpd_INFOFIFOscreen(artistAlbumTitle, paused="pause" in state)
        do_mpd_LCDscreen(artistAlbumTitle)


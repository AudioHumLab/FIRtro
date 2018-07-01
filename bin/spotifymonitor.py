#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
    Script daemon que atiende eventos GLib de Spotify desktop client y 
    los comunica a los server de display y a la web a través de server.py
"""

# v1.0 (formerly 'spotify2lcd.py')
# - Comprobamos que gi es un repositorio Python oficial.
# - Bucle inicial de espera hasta conectar con el server LCDproc
# v1.1
# - Se unifica la comunicación con los displays LCD e INFOFIFO
#   y con el server.py que actualizará la web de control

# Este código está basado en 'example.py' de https://github.com/acrisci/playerctl
# Más info sobre como interactuar con un cliente Spotify en Linux:
# https://wiki.archlinux.org/index.php/spotify

# Dependencia: python-gi
# gi.repository is the Python module for PyGObject (which stands for Python GObject introspection)
# which holds Python bindings and support for the GTK+ 3 toolkit and for the GNOME apps.
# See https://wiki.gnome.org/Projects/PyGObject
# > apt list python-gi
# python-gi/xenial,now 3.20.0-0ubuntu1 amd64 [instalado, automático]
# > aptitude search python-gi
# i A python-gi                                 - Python 2.x bindings for gobject-introspection libra

# IMPORTANTE:
# Este código solo funcionará si es invocado desde una sesión en un escritorio local que corra Spotify.
# NO funcionará desde una sesión remota ssh a una máquina en cuyo escritorio corra Spotify,
# debido a que no disponemos de acceso a la sesión DBus del escritorio:
#   > playerctl --list-all
#   No players were found
#   > dbus-send --print-reply --dest=org.mpris.MediaPlayer2.spotify /org/mpris/MediaPlayer2 org.mpris.MediaPlayer2.Player.PlayPause
#   Error org.freedesktop.DBus.Error.ServiceUnknown: The name org.mpris.MediaPlayer2.spotify was not provided by any .service files

# Interfaz mpris para interactuar con un player de escritorio
import gi
gi.require_version('Playerctl', '1.0')
from gi.repository import Playerctl, GLib

from sys import argv as sys_argv, path as sys_path
from time import sleep
from subprocess import check_output

# clientes para interactuar con los servidores de DISPLAYs de FIRtro
import client_lcd as cLCD
import client_infofifo as cFIFO
# cliente para interactuar con el server, que trasladará los metadata a la web de FIRtro
import client as cFIRtro
# Usamos json para entregar los metadata a través del socket tcp con server.py
import json
# Acceso a la configuracion de FIRtro:
import getconfig

def input_name():
    # función auxiliar para conocer el nombre de la entrada actual
    try:
        tmp = check_output('grep "input =" /home/firtro/audio/status', shell=True)
        return tmp.split()[-1]
    except:
        return ""

def do_spotify_send_metadata(artistAlbumTitle, paused=False, address="localhost", port=getconfig.control_port):
    # aux para enviar metadatas en formato json a un server
    artist, album, title = artistAlbumTitle
    if paused: state = "pause"
    else:      state = "play" 
    metaDict = {"player":"spotify", 
                "metadata":{"artist":artist, "album":album, "title":title, 'state':state} }
    metaJson = json.dumps(metaDict)
    cFIRtro.firtro_socket(metaJson, quiet=True)

def do_spotify_LCDscreen(artistAlbumTitle, speed=3):
    # aux para printar los 3 elementos de artistAlbumTitle en el LCD
    artist, album, title = artistAlbumTitle
    speed = str(speed)
    # creamos la pantalla
    cLCD.create_screen("spotify_scr1", duration=10)
    # comandos para la linea 1: widget de título
    w1_add = "widget_add spotify_scr1 w1 title"
    w1_set = "widget_set spotify_scr1 w1 \ \ \ Spotify\ \ \ \ "
    # comandos para las lineass 2-4: widgets del artista, album y pista
    w2_add = "widget_add spotify_scr1 w2 scroller"
    w3_add = "widget_add spotify_scr1 w3 scroller"
    w4_add = "widget_add spotify_scr1 w4 scroller"
    w2_set = "widget_set spotify_scr1 w2 1 2 20 2 m " + speed + " " + artist.replace(" ", "\ ")
    w3_set = "widget_set spotify_scr1 w3 1 3 20 3 m " + speed + " " + album.replace(" ", "\ ")
    w4_set = "widget_set spotify_scr1 w4 1 4 20 4 m " + speed + " " + title.replace(" ", "\ ")
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
    # la sesion no disppne de conexión DBUS con Spotify
    # Creamos la pantalla
    cLCD.create_screen("static", duration=0)
    # Comandos para la linea 1: widget de título
    w1_add = "widget_add static w1 title"
    w1_set = "widget_set static w1 SIN\ CONEXION\ Spotify"
    cLCD.cmd_s(w1_add)
    cLCD.cmd_s(w1_set)

def do_spotify_INFOFIFOscreen(artistAlbumTitle, paused=False):
    # aux para printar los 3 elementos de artistAlbumTitle en la INFOFIFO
    artist, album, title = artistAlbumTitle
    if paused: state = "pause"
    else:      state = "play" 
    d = {'artist':artist, 'album':album, 'title':title, 'state':state}
    jsonMetadata = json.dumps(d)
    # Info al server_infofifo en formato JSON con etiqueta previa:
    cFIFO.open()
    cFIFO.cmd_s( "Spotify " + jsonMetadata)
    cFIFO.close()

def do_static_INFOFIFOscreen():
    # aux para printar una pantalla estática indicando que 
    # la sesion no disppne de conexión DBUS con Spotify
    artist = 'NOT connected to Spotify'
    d = {'artist':artist}
    jsonMetadata = json.dumps(d)
    cFIFO.open()
    cFIFO.cmd_s( "Spotify " + jsonMetadata)
    cFIFO.close()

def get_artistAlbumTitle(e):
    global artistAlbumTitle
    if 'xesam:artist' in e.keys() and 'xesam:title' in e.keys():
        artist = e['xesam:artist'][0]
        album  = e['xesam:album']
        title =  e['xesam:title']
        artistAlbumTitle = [artist, album, title]
        return artistAlbumTitle
    else:
        artistAlbumTitle = ["unknown artist", "", ""]
        return artistAlbumTitle

def on_metadata(player, e):
    """ Handler para cuando ocurre UN CAMBIO DE METADATA en Spotify """
    if use_lcd:
        do_spotify_LCDscreen(get_artistAlbumTitle(e), speed=2)
    if use_infofifo:
        do_spotify_INFOFIFOscreen(get_artistAlbumTitle(e), paused=False)
    if use_firtro:
        do_spotify_send_metadata(get_artistAlbumTitle(e), paused=False)

def on_play(player):
    """ Handler para cuando se INICIA la reproducción en Spotify """
    if use_lcd:
        # Restaura el título de la screen de Spotify quitando el indicador PAUSED
        cLCD.cmd_s("widget_set spotify_scr1 w1 \ \ \ Spotify\ \ \ \ ")
    if "spotify" in input_name().lower():
        if use_lcd:
            # recupera la prioridad normal de la screen LCD de Spotify
            cLCD.cmd_s("screen_set spotify_scr1 -priority info")
        if use_infofifo:
            # printa metadata en INFOFIFO
            do_spotify_INFOFIFOscreen(artistAlbumTitle, paused=False)
        if use_firtro:
            do_spotify_send_metadata(artistAlbumTitle, paused=False)

def on_pause(player):
    """ Handler para cuando se PAUSA Spotify """
    if use_lcd:
        # Modifica el título de la screen LCD de Spotify añadendo el indicador PAUSED
        cLCD.cmd_s("widget_set spotify_scr1 w1 Spotify\ PAUSED")
        if not "spotify" in input_name().lower():
            # opc.A borra la screen de Spotify
            #cLCD.delete_screen("spotify_scr1")
            # opc.B deja la screen de Spotify en background
            cLCD.cmd_s("screen_set spotify_scr1 -priority background")
    if use_infofifo:
        do_spotify_INFOFIFOscreen(artistAlbumTitle, paused=True)
    if use_firtro:
        do_spotify_send_metadata(artistAlbumTitle, paused=True)

def try_INFOFIFO_server():
    i = 0
    while i < 5:
        if not cFIFO.open():
            sleep(.2)
            cFIFO.close()
            print "(spotifymonitor) ERROR conectando con el server FIFO"
        else:
            sleep(.2)
            cFIFO.close()
            print "(spotifymonitor) conectado al server FIFO"
            return True
        sleep(1)
        i += 1
    return False

def try_LCD_server(server):
    #
    # (!) IMPORTANTE: aquí no hacemos close() del socket ya que mantenemos
    #                 la conexión con el LCDd para ir cambiando las pantallas...
    i = 0
    while i < 5:
        if cLCD.open("spotify_client", server):
            print "(spotifymonitor) conectado al server LCDd"
            return True
        sleep(1)
        i += 1
    cLCD.close()
    print "(spotifymonitor) ERROR conectando con el server LCDd"
    return False

def try_FIRtro():
    i = 0
    while i < 5:
        if cFIRtro.firtro_socket("close", quiet=True)[:2] == "OK":
            print "(spotifymonitor) conectado a FIRtro (server.py)"
            return True
        sleep(1)
        i += 1
    print "(spotifymonitor) ERROR conectando a FIRtro (server.py)"
    return False

if __name__ == "__main__":

    if len(sys_argv) > 1:
        print __doc__
        raise SystemExit, 0

    use_infofifo = try_INFOFIFO_server()
    use_lcd =      try_LCD_server(getconfig.LCD_server_addr)
    use_firtro =   try_FIRtro()

    # Intenta conexión con SPOTFY usando una instancia Playerctl, que es
    # una interfaz dbus mpris para hablar con un player de un desktop.
    player = Playerctl.Player(player_name='spotify')
    if not player.props.status:
        if use_lcd:
            do_static_LCDscreen()
        if use_infofifo:
            do_static_INFOFIFOscreen()
        if use_firtro:
            do_spotify_send_metadata(["not connected to Spotify", "", ""])
        print "(spotifymonitor) ERROR conectando con SPOTIFY Desktop"
        raise SystemExit, 0

    # EVENTOS atendidos y HANDLERS asociados:
    player.on('play', on_play)
    player.on('pause', on_pause)
    player.on('metadata', on_metadata)

    # BUCLE PRINCIPAL: waits for GLib events
    mainGlibLoop = GLib.MainLoop()
    mainGlibLoop.run()


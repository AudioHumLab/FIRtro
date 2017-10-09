#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
    Script daemon que atiende eventos GLib de Spotify y los comunica al server LCDd
    Uso:
        spotify2lcd.py host:port
"""

# spotify2lcd.py
# v1.0
# - Comprobamos que gi es un repositorio Python oficial.
# - Bucle inicial de espera hasta conectar con el server LCDproc

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

import gi
gi.require_version('Playerctl', '1.0')
from gi.repository import Playerctl, GLib

from sys import argv as sys_argv, path as sys_path
from time import sleep
from subprocess import check_output

# cliente comun para interactuar con un servidor LCDproc
import client_lcd as cLCD

def input_name():
    # función auxiliar para conocer el nombre de la entrada actual
    try:
        tmp = check_output('grep "input =" /home/firtro/audio/status', shell=True)
        return tmp.split()[-1]
    except:
        return ""

def do_spotify_screen(artistAlbumTitle, speed=3):
    # aux para printar los 3 elementos de artistAlbumTitle en el LCD
    #print artistAlbumTitle  # debug
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

def do_static_screen():
    # aux para printar una pantalla estática indicando que 
    # la sesion no disppne de conexión DBUS con Spotify

    # creamos la pantalla
    cLCD.create_screen("static", duration=0)
    # comandos para la linea 1: widget de título
    w1_add = "widget_add static w1 title"
    w1_set = "widget_set static w1 Spotify\ (not\ connected)"

def on_metadata(player, e):
    # handler para cuando hay un cambio de metadata en Spotify
    if 'xesam:artist' in e.keys() and 'xesam:title' in e.keys():
        artist_title = '{artist} - {title}'.format(artist=e['xesam:artist'][0], title=e['xesam:title'])
        #print 'Spotify playing: ' + artist_title

        artist = e['xesam:artist'][0]
        album  = e['xesam:album']
        title =  e['xesam:title']
        artistAlbumTitle = [artist, album, title]
        do_spotify_screen(artistAlbumTitle, speed=2)

def on_play(player):
    # Handler para cuando se inicia la reproducción en Spotify
    #print 'Spotify playing at volume {}'.format(player.props.volume)
    # restaura el título de la screen de Spotify quitando el indicador PAUSED
    cLCD.cmd_s("widget_set spotify_scr1 w1 \ \ \ Spotify\ \ \ \ ")
    if "spotify" in input_name().lower():
        # recupera la prioridad normal de la screen de Spotify
        cLCD.cmd_s("screen_set spotify_scr1 -priority info")

def on_pause(player):
    # Handler para cuando se pausa Spotify
    #print 'Paused the song: {}'.format(player.get_title())
    # modifica el título de la screen de Spotify añadendo el indicador PAUSED
    cLCD.cmd_s("widget_set spotify_scr1 w1 Spotify\ PAUSED")
    if not "spotify" in input_name().lower():
        # opc.A borra la screen de Spotify
        #cLCD.delete_screen("spotify_scr1")
        # opc.B deja la screen de Spotify en background
        cLCD.cmd_s("screen_set spotify_scr1 -priority background")

if __name__ == "__main__":

    if len(sys_argv) == 2:
        server = sys_argv[1]
    else:
        print __doc__
        exit()

    # Intenta conectar al server LCDd
    while True:
        if cLCD.open("spotify_client", server):
            print "(spotify2lcd.py) se ha conectado con el server " + server
            break
        sleep(5)

    # crea una instancia de Playerctl, que es una interfaz dbus mpris para hablar con los player de un escritorio.
    player = Playerctl.Player(player_name='spotify')

    # Eventos atendidos y sus handlers
    player.on('play', on_play)
    player.on('pause', on_pause)
    player.on('metadata', on_metadata)

    # Ejemplos de interacción con el player:
    # player.play()
    # print player.get_artist()
    # player.next()

    # BUCLE PRINCIPAL: wait for GLib events
    mainGlibLoop = GLib.MainLoop()
    mainGlibLoop.run()


#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
    Script que atiende eventos GLib de Spotify y los comunica al server LCDd
"""
# spotify2lcd.py
# v1.0
# - vemos arriba que gi es una libreria oficial, ¡uff! qué susto.

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
# Este código solo funcinará si es invocado desde una sesión en un escritorio local que corra Spotify.
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

# acceso a 'server_lcd_big.py' de /home/firtro/bin
from os import path as os_path
sys_path.append("/home/firtro/bin")
import server_lcd_big as lcd

def spotify_LCD(artistAlbumTitle, speed=3):
    # aux para printar los 3 elementos de artistAlbumTitle en el LCD
    #print artistAlbumTitle  # debug
    artist, album, title = artistAlbumTitle

    speed = str(speed)
    lcd._create_screen("spotify_scr1", duration=10)
    w1_add = "widget_add spotify_scr1 w1 title"
    w1_set = "widget_set spotify_scr1 w1 \ \ \ Spotify\ \ \ \ "

    w2_add = "widget_add spotify_scr1 w2 scroller"
    w3_add = "widget_add spotify_scr1 w3 scroller"
    w4_add = "widget_add spotify_scr1 w4 scroller"
    w2_set = "widget_set spotify_scr1 w2 1 2 20 2 m " + speed + " " + artist.replace(" ", "\ ")
    w3_set = "widget_set spotify_scr1 w3 1 3 20 3 m " + speed + " " + album.replace(" ", "\ ")
    w4_set = "widget_set spotify_scr1 w4 1 4 20 4 m " + speed + " " + title.replace(" ", "\ ")

    lcd.lcd_cmd_s(w1_add)
    lcd.lcd_cmd_s(w2_add)
    lcd.lcd_cmd_s(w3_add)
    lcd.lcd_cmd_s(w4_add)
    lcd.lcd_cmd_s(w1_set)
    lcd.lcd_cmd_s(w2_set)
    lcd.lcd_cmd_s(w3_set)
    lcd.lcd_cmd_s(w4_set)


def on_metadata(player, e):
    # handler para cuando hay un nuevo metadata en Spotify
    if 'xesam:artist' in e.keys() and 'xesam:title' in e.keys():
        print 'Now playing:'
        artist_title = '{artist} - {title}'.format(artist=e['xesam:artist'][0], title=e['xesam:title'])
        print artist_title

        artist = e['xesam:artist'][0]
        album  = e['xesam:album']
        title =  e['xesam:title']
        artistAlbumTitle = [artist, album, title]
        spotify_LCD(artistAlbumTitle, speed=2)

def on_play(player):
    # handler para cuando se inicia la reproducción en Spotify
    print 'Playing at volume {}'.format(player.props.volume)

def on_pause(player):
    # handler para cuando se pausa Spotify
    print 'Paused the song: {}'.format(player.get_title())
    # borra del LDC la pantalla de Spotify si se pausa
    lcd._delete_screen("spotify_scr1")

if __name__ == "__main__":

    if len(sys_argv) > 1:
        print __doc__
        exit()

    # crea cliente conectado al server LCDd del sistema
    lcd.crea_cliente("spotify_client")
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

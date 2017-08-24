#!/usr/bin/python
#coding=utf-8
# from __future__ import with_statement # This isn't required in Python 2.6

# Copyright (C) 2013 Roberto Ripio, Alberto Miguelez & Rafael Sanchez
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

# from __future__ import with_statement # This isn't required in Python 2.6

from ConfigParser import RawConfigParser
from basepaths import config_folder,media_config_filename
import os
import sys
import subprocess
import mpd

# Variables
tracks = {} # Diccionario para almacenar las pistas de cada medio
config = RawConfigParser()
#config_path=os.path.join(os.path.abspath(os.path.dirname(__file__)), 'mmedia.cfg') # Para buscarlo en el mismo directorio donde está el script actual
config_path=os.path.join(config_folder, media_config_filename)  # Ruta al fichero de configuracion

# Nos aseguramos de que existe el fichero
if not os.path.isfile(config_path):
    print "Can't find configuration file",config_path
    sys.exit(-1)

# Si existe, leemos las secciones correspondientes
try:
    config_file = open(config_path)
    config.readfp(config_file)
    config_file.close
    devices = config.get('main','devices').split(',')
    mount_base = config.get ('main','mount_base')
    playlist_mode = config.getint('playlist','mode')
    playlist_name = config.get ('playlist','name')
    playlist_previous_name = config.get ('playlist','previous_name')
    playlist_path = config.get ('playlist','path')
    file_filter = config.get ('playlist','file_filter')
    file_exclude = config.get ('playlist','file_exclude')
    mpd_socket = config.get('mpd','socket')
except:
    print "Error in configuration file"
    sys.exit(-1)

def start():
    # Declaramos estas variables como globales ya que sino da un error UnboundLocalError
    global file_filter
    global file_exclude
    # Test de impresion de opciones
    print
    print "Devices:",', '.join(devices)
    print "Mount point:",mount_base
    print "Playlist mode:",playlist_mode
    if not file_filter: print "File filter: none"
    else: print "File filter: ", ', '.join(file_filter)
    if not file_exclude: print "Excluded files: none"
    else: print "Excluded files:", ', '.join(file_exclude.split(','))
    print

    # Si no se ha especificado ningún filtro de extensiones, se obtienen todas las soportadas por mpd
    if not file_filter:
        # Nos conectamos a mpd
        client = mpd.MPDClient()
        try:
            client.connect(mpd_socket,0)
        except:
            print "Can't connect to mpd"
            sys.exit(-1)
        formats=[]
        for decoder in client.decoders():
            for key, values in decoder.items():
                if key=='suffix':
                    if type(values)==list: formats.extend(values)
                    else: formats.append(values)
        client.close()
    else: formats=file_filter.split(',')

    # Ponemos los puntos a las extensiones, para afinar mas el filtro
    for index in range(len(formats)):
        formats[index]='.'+formats[index]

    # Se convierte a tuple porque el método endswith no admite listas
    file_filter=tuple(formats)     

    if file_exclude:
        file_exclude=file_exclude.split(',')
        # Ponemos los puntos a las extensiones, para afinar mas el filtro
        for index in range(len(file_exclude)):
            file_exclude[index]='.'+file_exclude[index]
        # Se convierte a tuple porque el método endswith no admite listas
        file_exclude=tuple(file_exclude)
    else: file_exclude=()
    # Desmontamos las unidades y borramos las playlists
    eject()
    # Extraemos el contenido para cada dispositivo y lo guardamos en un diccionario
    print "Mounting devices..."
    for device in devices:
        mount_point = mount_base+'/'+device # Obtenemos el punto de montaje
        mount_result=subprocess.call('mount /dev/' + device + '>/dev/null 2>&1',shell=True) # Se intenta montar
        if (mount_result == 0):
            print mount_point,"=> OK. Scanning files..."
            # Recorremos todos los ficheros de forma recursiva
            for path, dirs, files in os.walk(mount_point):
                for name in files:
                    if (name.endswith(file_filter) & (not name.startswith(".")) & (not name.endswith(file_exclude))):  # Filtramos las extensiones, para añadir solo archivos válidos, excluimos ocultos y descartamos las extensiones especificadas
                        track = os.path.join(path, name)
                        print '\t'+track
                        tracks.setdefault(device,[]).append(track) # Almacenamos dispositivo-pista en el diccionario
        else: print mount_point,"=> Not available"

    if not tracks:
        print "\nNo suitable media files found!"
        sys.exit()

    # Extraemos los valores del diccionario
    tracks_items=tracks.items()

    if playlist_mode == 0:
        # Añadimos todo a la lista actual
        # Nos conectamos a mpd
        client = mpd.MPDClient()
        try:
            client.connect(mpd_socket,0)
        except:
            print "Can't connect to mpd"
            sys.exit(-1)
        # Salvamos el contenido si asi se especifica, borrando antes la lista si existe
        if (playlist_previous_name):
            print "Saving current playlist..."
            try:
                client.rm(playlist_previous_name)
            except: pass
            client.save(playlist_previous_name)
            client.clear()
        # Añadimos el contenido escaneado
        print "Adding media files to mpd..."
        for device,track_list in tracks_items:
            for track in track_list:
                try:
                    client.add("file://"+track)
                except: print "\tFile %s can't be added" %track
        client.close()
    elif playlist_mode == 1:
        # Añadimos todo a una lista independiente
        print "Playlist mode not supported"
        sys.exit(-1)
        playlist_fullpath=os.path.join(playlist_path,playlist_name)+'.'+playlist_extension
        playlist = open (playlist_fullpath, 'w')
        print "\nGenerating playlist",playlist_fullpath+"..."
        for device,track_list in tracks_items:
            for track in track_list:
                playlist.write(track+"\n")
        playlist.close()
    elif playlist_mode == 2:
        # Añadimos el contenido a una lista independiente por dispositivo
        print "Playlist mode not supported"
        sys.exit(-1)
        for device,track_list in tracks_items:
            playlist_fullpath=os.path.join(playlist_path,playlist_name)+'_'+device+'.'+playlist_extension
            print "\nGenerating playlist",playlist_fullpath+"..."
            playlist = open (playlist_fullpath, 'w') 
            for track in track_list:
                playlist.write(track+"\n")
            playlist.close()
    else:
        print"\nError: Invalid playlist mode"
        sys.exit(-1)

def stop():
    if playlist_mode == 0:
        # Nos conectamos a mpd
        client = mpd.MPDClient()
        try:
            client.connect(mpd_socket,0)
        except:
            print "Can't connect to mpd, previous playlist can't be restored"
        else:
            print "Restoring previous playlist..."
            client.clear()
            try:
                client.load(playlist_previous_name)
            except: pass
            client.close()
    eject()
    #for device in devices:
        #mount_point = mount_base+'/'+device # Obtenemos el punto de montaje
        #playlist_fullpath=os.path.join(playlist_path,playlist_name)+'_'+device+'.'+playlist_extension
        #try:
        #    os.remove (playlist_fullpath)
        #except: pass
    # Borramos la playlist de los modos 0 y 1
    #playlist_fullpath=os.path.join(playlist_path,playlist_name)+'.'+playlist_extension
    #try:
    #   os.remove (playlist_fullpath)
    #except: pass

def eject():
    # Desmontamos las unidades
    for device in devices:
        mount_point = mount_base+'/'+device # Obtenemos el punto de montaje
        subprocess.call('umount /dev/' + device + '>/dev/null 2>&1',shell=True)
        print "Unmounting %s..." %device

if __name__ == "__main__":
    if len (sys.argv)>1:
        if (sys.argv[1]=='eject'):
            stop()
            print "Done"
        else:
            print "Command %s not valid" %('"'+sys.argv[1]+'"')
            print "Use: media [eject]"
    else:
        start()
        print "Done"
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

from __future__ import print_function

import cdrom, mpd, DiscID, CDDB
from configobj import ConfigObj, ConfigObjError
from basepaths import config_folder,mcd_config_filename
from ConfigParser import RawConfigParser
import os
import fileinput
import sys

config = RawConfigParser()

#config_path=os.path.join(os.path.abspath(os.path.dirname(__file__)), 'mmedia.cfg') # Para buscarlo en el mismo directorio donde está el script actual
config_path=os.path.join(config_folder, mcd_config_filename)  # Ruta al fichero de configuracion

# Nos aseguramos de que existe el fichero
if not os.path.isfile(config_path):
    print ("Can't find configuration file %s" %config_path)
    sys.exit(-1)

# Si existe, leemos las secciones correspondientes
try:
    config_file = open(config_path)
    config.readfp(config_file)
    config_file.close
    print ("config file", config_file)   
    default_track_name = config.get('playlist','default_track_name')
    previous_name = config.get('playlist','previous_name')
    playlist_name = config.get('playlist','playlist_name')
    playlist_path = config.get('playlist','playlist_path')
    cddb_path = config.get('playlist','cddb_path')
    mpd_port = config.get('mpd','port')
except:
    print ("Error in configuration file")
    sys.exit(-1)
    
playlist_fullpath = os.path.join(playlist_path, playlist_name)
print (playlist_fullpath)

# Gets track lengths
device = cdrom.open("/dev/sr0") #cambiar esta linea con el nombre del cdrom
try:
    (first, num_tracks) = cdrom.toc_header(device)
except:
    print ("no medium found")
    sys.exit(-1)
    
track_length = [] # track_length in seconds
track_limits = []
track_prefix = []
track_title = []
disk_title = []

for i in range(num_tracks):
	(min, sec, frame) = cdrom.toc_entry(device, i+1)
	track_limits.append (60*min + sec + frame/75.)
	
(min, sec, frame) = cdrom.leadout(device)
track_limits.append (60*min + sec + frame/75.)

for i in range(num_tracks):
	track_length.append (track_limits[i+1] - track_limits[i])
	track_prefix.append ("%02d. " % (i+1))
	track_title.append (track_prefix [i] + default_track_name)

status2 = 0
disc_id = DiscID.disc_id(device)
cddb_id = hex(disc_id[0])[2:] # magic id string

# looks for cd in local database
cddb_fullpath = cddb_path+cddb_id
print ("cddb_fullpath", cddb_fullpath)

cddb_local = False
if os.path.exists(cddb_fullpath):
    cddb_local = True
    # check for the insidious last line "."
    # to preserve file timestamp if all correct
    insidious_last_line = False
    for line in fileinput.input(cddb_fullpath):
        if line == '.\n': insidious_last_line = True
    # filters the insidious last line ".", if any
    if insidious_last_line:
        for line in fileinput.input(cddb_fullpath,inplace=1):
            if line != '.\n':
                print (line, end="")
    # reads local cddb file
    try:
        cddb_file = ConfigObj(cddb_fullpath)
        disk_title = info2['DTITLE'].split(' / ')
        for i in range(num_tracks):
            track_title[i] = track_prefix [i] + cddb_file['TTITLE%s' % (i)]
        print ("Used local cddb data.")
    except (ConfigObjError) :
        print ("Error in local cddb file")
        cddb_local = False

if not cddb_local:
    (status1, info1) = CDDB.query(disc_id)
    print ("query status = %s" % status1)
    if status1 == 200: # Entry exist
        print (info1['title'] + " // " + info1['category'])
        (status2, info2) = CDDB.read(info1['category'], info1['disc_id'])
        print ("read status = %s" % status2)
        readtracks = True
    elif status1 == 210: # Various entries exist, choose blindly the first
        print (info1[0]['title'] + " // " + info1[0]['category'])
        (status2, info2) = CDDB.read(info1[0]['category'], info1[0]['disc_id'])
        print ("read status = %s" % status2)
    if status2 == 210: # Start reading tracks
        disk_title = info2['DTITLE'].split(' / ')
        for i in range(num_tracks):
            track_title[i] = track_prefix [i] + info2['TTITLE%s' % (i)]

# Makes playlist
playlist = open (playlist_fullpath, 'w')
print ("nombre",playlist)
playlist.write ('<?xml version="1.0" encoding="UTF-8"?>\n')
playlist.write ('<playlist version="1" xmlns="http://xspf.org/ns/0/">\n')
playlist.write ("\t<trackList>\n")
for i in range(num_tracks):
    playlist.write ("\t\t<track>\n")
    playlist.write ("\t\t\t<location>cdda:///%s</location>\n" %(i+1))
    if len(disk_title)>0:  
        disk_title[0] = disk_title[0].replace("&", "&amp;");
        playlist.write ("\t\t\t<creator>"+disk_title[0]+"</creator>\n")
    if len(disk_title)>1:
        disk_title[1] = disk_title[1].replace("&", "&amp;");
        playlist.write ("\t\t\t<album>"+disk_title[1]+"</album>\n")
    if cddb_local:   # local files are utf-8 already
        track_title[i] = track_title[i].replace("&", "&amp;");
        playlist.write ("\t\t\t<title>"+track_title[i]+"</title>\n")
    else:
        track_title[i] = track_title[i].replace ("&","&amp;");
        playlist.write (("\t\t\t<title>"+track_title[i]+"</title>\n").decode('latin-1').encode('utf-8'))
    playlist.write ("\t\t\t<duration>%d%s" %((track_length[i]*1000), "</duration>\n"))
    playlist.write ("\t\t</track>\n")
playlist.write ("\t</trackList>\n")
playlist.write ("</playlist>\n")
playlist.close()

# Loads playlist
client = mpd.MPDClient()           # create client object
try:
    client.connect("localhost", mpd_port) # connect to localhost:6600
except:
    print ("Can't connect to mpd")
    sys.exit(-1)
try:
    client.rm(previous_name)
except: #  CommandError
    pass
client.save(previous_name)
client.clear()
print ("playlist name.." + playlist_name)
print ("playlist path.." + playlist_path)
client.load(playlist_name)
client.close()

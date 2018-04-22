#!/usr/bin/python
#coding=utf-8
# from __future__ import with_statement # This isn't required in Python 2.6

# v1.1
#  Para evitar el siguiente error cuando un script ejecuta
#
#   'import getstatus'  o  'from getstatus import *'
#
#  pero todavía se está completando la escritura de audio/status:
#
#      File "/home/firtro/bin/getstatus.py", line 15, in <module>
#        system_eq = status.get('room EQ', 'system_eq')
#      File "/usr/lib/python2.7/ConfigParser.py", line 330, in get
#        raise NoSectionError(section)
#      ConfigParser.NoSectionError: No section: 'room EQ'
#
# Fix: la lectura se supervisa en un try / except, con un bucle de reintentos.


from ConfigParser import RawConfigParser
from basepaths import *
from time import sleep

status_path = config_folder + status_filename
status = RawConfigParser()

t = 0
while True:

    try:

        statusfile = open(status_path)
        status.readfp(statusfile)
        statusfile.close

        #[room EQ]
        system_eq = status.get('room EQ', 'system_eq')
        drc_eq = status.get('room EQ', 'drc_eq')
        peq = status.get('room EQ', 'peq')
        peqdefeat = status.get('room EQ', 'peqdefeat')
        #[recording EQ]
        treble = status.getfloat('recording EQ', 'treble')
        bass = status.getfloat('recording EQ', 'bass')
        loudness_ref = status.getfloat('recording EQ', 'loudness_ref')
        loudness_track = status.getboolean('recording EQ', 'loudness_track')
        #[level]
        replaygain_track = status.getboolean('level', 'replaygain_track')
        level = status.getfloat('level', 'level')
        headroom = status.getfloat('level', 'headroom')
        balance = status.getfloat('level', 'balance')
        #[general]
        fs = status.get('general', 'fs')
        filter_type = status.get('general', 'filter_type')
        preset = status.get('general', 'preset')
        muted = status.getboolean('general', 'muted')
        polarity = status.get('general', 'polarity')
        clock = status.get('general', 'clock')
        #[inputs]
        input_name = status.get('inputs', 'input')
        mono =  status.get('inputs', 'mono')
        radio = status.get('inputs', 'radio')
        radio_prev = status.get('inputs', 'radio_prev')
        resampled = status.get('inputs', 'resampled')
        break

    except:
        t += 1
        sleep (.2)
        if t > 5:
            print "(getstatus.py) ERROR leyendo audio/status" 
            break

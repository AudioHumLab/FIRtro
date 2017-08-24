#!/usr/bin/python
#coding=utf-8
# from __future__ import with_statement # This isn't required in Python 2.6

from ConfigParser import RawConfigParser
from basepaths import *

status_path = config_folder + status_filename
status = RawConfigParser()
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

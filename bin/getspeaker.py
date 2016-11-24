#!/usr/bin/python
#coding=utf-8
# from __future__ import with_statement # This isn't required in Python 2.6

import ConfigParser
from getconfig import *

speaker_path = loudspeaker_folder + loudspeaker + '/' + speaker_filename

speaker = ConfigParser.RawConfigParser()
speakerfile = open(speaker_path)
speaker.readfp(speakerfile)
speakerfile.close

#[equalization]
system_eq = speaker.getboolean('equalization', 'system_eq')
room_gain = speaker.getfloat('equalization', 'room_gain')
house_corner = speaker.getfloat('equalization', 'house_corner')
house_atten = speaker.getfloat('equalization', 'house_atten')
#[calibration]
ref_level_gain = speaker.getfloat('calibration', 'ref_level_gain')

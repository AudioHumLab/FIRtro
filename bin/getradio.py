#!/usr/bin/python
#coding=utf-8
# from __future__ import with_statement # This isn't required in Python 2.6

from ConfigParser import RawConfigParser
from getconfig import *

channels_filename = 'radio'

channels_path = config_folder + channels_filename

channels = RawConfigParser()
channelsfile = open(channels_path)
channels.readfp(channelsfile)
channelsfile.close


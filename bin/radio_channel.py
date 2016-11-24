#!/usr/bin/python
#coding=utf-8
# from __future__ import with_statement # This isn't required in Python 2.6

import sys
from subprocess import *
#import str
from getstatus import *
from getradio import *

def messages():
    print "Canal " + radio
    
if len(sys.argv) > 1:
    name = sys.argv[1]
else:
    messages()
    exit()
    
old_input_name = input_name
    
if name == "-c":
    pass
elif channels.has_option("channels", name):
    radio = name
        
else:
    print "El canal \"" + name + "\" no existe"
    exit()

channel_name = channels.get("channels", radio)
if channel_name == "":
    print "El canal \"" + name + "\" no está configurado"
    exit()
radio_play = Popen('echo loadfile dvb://' + "'" + channel_name +"'"+' > ' + tdt_fifo, shell=True)

messages()

status.set('inputs', 'radio', radio)

statusfile = open(status_path, 'w')
status.write(statusfile)
statusfile.close


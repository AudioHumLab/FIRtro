#!/usr/bin/python
#coding=utf-8
# from __future__ import with_statement # This isn't required in Python 2.6

# Calcula la curva target de ecualización, o ecualización de sistema

import ConfigParser
from curves import *
from numpy import *
from getspeaker import *
from getconfig import *


# SYSTEM EQUALIZATION
freq = loadtxt(freq_path)
eq_curve = zeros(len(freq))

if system_eq:
    if house_atten>0:
        house = HouseCurve (freq, house_corner, house_atten)
    else:
        house = zeros(len(freq))
    room = RoomGain (freq, room_gain)
    eq_curve = eq_curve + house + room

eq_str = ""
for index in range(len(freq)):
    eq_str = eq_str + str(freq[index]) + '/' + str(eq_curve[index]) + ", "

# Write data to file
savetxt (syseq_mag_path, eq_curve)
print "Curvas guardadas en " + syseq_mag_path


#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
convierte valores de Q a BW en octavas
"""

from sys import argv as sys_argv
import math

def bw2q(BW):
    """
    'http://www.bmltech.com/refbook/audio'
    """
    return math.sqrt(2**BW) / (2**BW -1)

if __name__ == '__main__':

    try:
        BW = float(sys_argv[1])
        print bw2q(BW)

    except:
        print __doc__


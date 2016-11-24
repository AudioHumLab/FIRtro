#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
convierte valores de Q a BW en octavas
"""

from sys import argv as sys_argv
import math

def q2bw(Q):
    """ http://www.rane.com/note167.html#qformula
        http://www.rane.com/note170.html
    """
    bw = 2.0 / math.log10(2.0) * math.log10( 0.5 * (1/Q + math.sqrt(1/Q**2 + 4)))
    return bw

def q2bw_v2(Q):
    """ http://www.musicdsp.org/files/Audio-EQ-Cookbook.txt
        FYI: The relationship between bandwidth and Q is
             1/Q = 2*sinh(ln(2)/2*BW*w0/sin(w0))     (digital filter w BLT)
        or   1/Q = 2*sinh(ln(2)/2*BW)             (analog filter prototype)
    """
    pass


if __name__ == '__main__':

    try:
        Q = float(sys_argv[1])
        print q2bw(Q)

    except:
        print __doc__


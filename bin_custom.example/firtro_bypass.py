#!/usr/bin/python
# -*- coding: utf-8 -*-
u""" 
    Script para medir las cajas sin ecualización alguna en el FIRtro:
    Se desconecta PEQ, Loudness, DRC, SYSEQ, Balance, Bass, Treble.
"""    
import jack
from sys import argv as sys_argv, path as sys_path
from time import sleep
from subprocess import call
sys_path.append("/home/firtro/bin")
import peq_control

def main():
    call('control "loudness_track_off"', shell=True)
    call('control "drc 0 "', shell=True)
    call('control "syseq_off"', shell=True)
    call('control "balance 0"', shell=True)
    call('control "bass 0"', shell=True)
    call('control "treble 0"', shell=True)
    call('control "input analog"', shell=True)
    call('control "level -10"', shell=True)
    call('control "peq_defeat"', shell=True)
    call('peq_control.py PEQdump', shell=True)
    call('peq_control.py "PEQbypass on"', shell=True)
    
if __name__ == "__main__":
    print __doc__
    main()
    print "(i) Level a -10 dB por prudencia, conviene revisarlo\n"




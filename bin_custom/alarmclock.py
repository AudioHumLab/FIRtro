#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    Use:
        alarmclock.py                  Print cron jobs for firtro
        alarmclock.py HH:MM [DoW]      Add an alarm clock on
        alarmclock.py HH:MM [DoW] off  Add an alarm clock off
        alarmclock.py -clear           Clear any 'alarmclock' entry job 
        alarmclock.py -edit            Edit userconfig.ini file 
        alarmclock.py --help           This help
"""
from sys import argv as sys_argv, exit as sys_exit
from subprocess import call, check_output
import firtroTasks as ft

alarmUserScript    = "/home/firtro/bin_custom/alarmclock.sh"
alarmOffUserScript = "/home/firtro/bin_custom/alarmclock_off.sh"

def appendAlarmClock(hora, DoW, offMode):
    if ":" in hora:    
        hh = hora.split(":")[0]
        mm = hora.split(":")[1]
    else:
        return False
    if not mm or not hh:
        return False
    if not offMode:
        if not ft.appendTaskINI(time=hora, DoW=DoW, task=alarmUserScript):
            return False
    else:
        if not ft.appendTaskINI(time=hora, DoW=DoW, task=alarmOffUserScript):
            return False
    return True

if __name__ == "__main__":
    
    hora = ""
    DoW  = "*"
    editMode = False
    clearMode = False
    offMode = False

    if sys_argv[1:]:
        for cosa in sys_argv[1:]:
            if ":" in cosa:
                hora = cosa
            elif ("-" in cosa and not "-h" in cosa) or "," in cosa or cosa.isdigit():
                DoW = cosa
            elif cosa == "off":
                offMode = True
            elif cosa == "-edit":
                editMode = True
            elif cosa == "-clear":
                clearMode = True
            elif "-h" in cosa:
                print __doc__
                sys_exit()
    else:
        ft.printCrontab()
        sys_exit()

    if hora:
        if appendAlarmClock(hora=hora, DoW=DoW, offMode=offMode):
            ft.printCrontab()
        else:
            print __doc__
            sys_exit()
    elif editMode:
        ft.editINI()
    elif clearMode:
        ft.clearINIalarmclock()
    else:
        print __doc__
    

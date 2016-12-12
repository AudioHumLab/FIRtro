#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    Use:
        alarmclock.py                Print cron jobs for firtro
        alarmclock.py  HH:MM [DoW]   Add an alarm clock
        alarmclock.py  clear         Clear any 'alarmclock' entry job 
        alarmclock.py  edit          Edit firtro.ini file 
        alarmclock.py  --help        This help
"""
from sys import argv as sys_argv, exit as sys_exit
from subprocess import call, check_output
import firtroTasks as ft

alarmUserScript = "/home/firtro/bin_custom/alarmclock.sh"

def appendAlarmClock(hora, DoW):
    if ":" in hora:    
        hh = hora.split(":")[0]
        mm = hora.split(":")[1]
    else:
        return False
    if not mm or not hh:
        return False
    
    if ft.appendTaskINI(time=hora, DoW=DoW, task=alarmUserScript):
        return True
    else:
        return False

if __name__ == "__main__":
    
    hora = ""
    DoW  = "*"
    editMode = False
    clearMode = False

    if sys_argv[1:]:
        for cosa in sys_argv[1:]:
            if ":" in cosa:
                hora = cosa
            elif ("-" in cosa and not "-h" in cosa) or "," in cosa or cosa.isdigit():
                DoW = cosa
            elif cosa == "edit":
                editMode = True
            elif cosa == "clear":
                clearMode = True
            elif "-h" in cosa:
                print __doc__
                sys_exit()
    else:
        ft.printCrontab()
        sys_exit()

    if hora:
        if appendAlarmClock(hora=hora, DoW=DoW):
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
    

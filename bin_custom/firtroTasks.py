#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    use:
        firtroTasks.py print | edit 

    This module is usually used by alarmclock.py script
"""
# v1.1 configobj sustituye a ConfigParser pq respeta los comentarios en el .INI

crontabFile = "/home/firtro/custom/firtroCrontab"
INIfile     = "/home/firtro/custom/firtro.ini"

from sys import argv as sys_argv
from subprocess import call, check_output
from configobj import ConfigObj
INI = ConfigObj(INIfile)

def printCrontab():
    entradas = []
    tmp = check_output("crontab -l", shell=True).split("\n")
    for linea in tmp:
        if not linea.strip().startswith("#"):
            if linea:
                entradas.append(linea.split())
    print "--- Cron jobs:"
    print "HH:MM  DoWeek   DoMonth   Month    COMMAND"
    for e in entradas:
        print e[1].rjust(2,"0") + ":" + e[0].rjust(2,"0") + "  " + \
              e[4].ljust(9) + e[2].ljust(10) + e[3].ljust(9) + " ".join(e[5:]) 

def readTasksINI():
    tasks = []
    INI.reload()
    tasksSection = INI["tasks"]
    for tnum in tasksSection.keys():
        task = tasksSection[tnum]
        if task: 
            tasks.append(task.split()[:4] + [" ".join(task.split()[4:])])
    return tasks

def appendTaskINI(time, DoW="*", DoM="*", Month="*", task=""):
    """ append a task, then update cron jobs 
    """
    tasksSection = INI["tasks"]
    newTaskNum = str( int(max(tasksSection.keys())) + 1 )
        
    tmp = time.ljust(7) + DoW.ljust(9) + DoM.ljust(10) + Month.ljust(9) + task
    INI["tasks"][newTaskNum] = tmp 
    INI.write()
    updateCrontab(readTasksINI())
    return True

def editINI():
    """ edit firtro.ini, then update cron jobs
    """
    call("nano " + INIfile, shell=True)
    updateCrontab(readTasksINI())
    printCrontab()

def updateCrontab(tasks):
    """ write tasks to a crontabFile
        then update crontrab with it
    """
    f = open(crontabFile, "w")
    f.write("#M H  DoM     Mon    DoW         command" + "\n")
    for t in tasks:
        # print t
        mm  = t[0].split(":")[1]
        hh  = t[0].split(":")[0]
        DoW = t[1]
        DoM = t[2]
        Mon = t[3]
        cmd = t[4]
        tmp = mm.ljust(3) + hh.ljust(3) + DoM.ljust(8) + Mon.ljust(7) + DoW.ljust(12) + cmd
        f.write(tmp + "\n")
    f.close()
    call("crontab " + crontabFile, shell=True)

def clearINIalarmclock():
    """ Borra las claves de la seccion [tasks] que sean de alarma
    """
    tasksSection = INI["tasks"]
    for tnum in tasksSection.keys():
        if "alarm" in tasksSection[tnum]:
            del tasksSection[tnum]
    INI.write()
    updateCrontab(readTasksINI())
    printCrontab()

if __name__ == "__main__":
    if sys_argv[1:]:
        if sys_argv[1].lower() == "print":
            printCrontab()
        elif sys_argv[1].lower() == "edit":
            editINI()
        else:
            print __doc__
    else:
        print __doc__

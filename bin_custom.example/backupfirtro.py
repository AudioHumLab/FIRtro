#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    v1.0
    Script para hacer backups de los archivos de FIRtro.

    Uso:
        backupfirtro.py [ -mirror | -dated [comentario] ]
        
    Configuración: 
        Definida en ~/custom/userconfig.ini  

    NOTAS:  
        No se permite ser root
        La opción "-mirror" vuelca la configuración actual.
        La opcion "-dated" permite añadir un "comentario" que se
        añadirá con la fecha al nombre de la carpeta de destino.
"""
#
# v1.0 no se considera comprimir archivos ya que un snapshot
# ocupa tan solo unos 20Mb aprox.
#
# v1.? pendiente considerar si es más adecuado usar 'Popen' en lugar de 'call'
#

from datetime import datetime
from os import environ
from sys import exit as sys_exit, argv as sys_argv
from ConfigParser import ConfigParser
from subprocess import call

# EL archivo de configuración personal de FIRtro
# contiene la configuración del backup.
configINI = ConfigParser()
configINI.read("/home/firtro/custom/userconfig.ini")

# Ejemplo en bash
#SRCPATH='/etc /home/firtro /usr/local/bin'
#SRCPATH='/home/firtro/'
#DSTPATH=root@192.168.1.4::NetBackup/FIRtro/
#DSTPATH='/media/sda1/firtroMirror'
#
#rsync -vaz \
#      --exclude '*.pyc'       \
#      --exclude '.client175'  \
#      --exclude 'music/'      \
#      --exclude 'tmp/'        \
#      --exclude 'www/music/'  \
#      $SRCPATH $DSTPATH/$DATE

def rsyncFirtro(mode, comments):
    cmd = "rsync -vaz"
    srcPath  = configINI.get("backup_origins", "firtro")

    if mode == "dated":
        now = datetime.now().strftime("%Y%m%d_%H%M%S")
        destPath = configINI.get("backup_destinations", "dated")

    elif mode == "mirror":
        destPath = configINI.get("backup_destinations", "mirror")
    else:
        return None

    if not srcPath.endswith("/"): srcPath += "/"
    if not destPath.endswith("/"): destPath += "/"

    if mode == "mirror":
        # borramos archivos extraños en el destino"
        cmd += " --delete"

    # añadimos todos los excludes en el comando
    for pattern in configINI.get("backup_patterns", "exclude").split():
        cmd += " --exclude " +  pattern
    cmd += " " + srcPath + " " + destPath

    if mode == "dated":
        # añadimos la fecha
        cmd += now + "_" + comments

    #print cmd
    call(cmd, shell=True)

if __name__ == "__main__":

    if 'root' in environ.get('USER'):
        print "chico malo no se puede ser root\n"
        sys_exit()

    comments = ""

    if sys_argv[1:] and sys_argv[1] in ("-mirror", "-dated"):

        if "mirror" in sys_argv[1]:
            rsyncFirtro("mirror", "")

        if "dated" in sys_argv[1]:
            if sys_argv[2]:
                comments = sys_argv[2]
            rsyncFirtro("dated", comments)
 
    else:
        print __doc__
        sys_exit()


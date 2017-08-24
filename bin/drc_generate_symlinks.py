#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
    Script para generar symlinks drc-X-Y para para compatibilidad con el script de control
    a partir de los pcm de los subdirectorios 'drc-X' de la carpeta del altavoz+Fs
    (Usado por brutefir_config.py)

    Uso desde la línea de comandos

        drc_generate_symlinks.py lspk/altavoz

'''
import sys, os

HOME = os.path.expanduser("~")
sys.path.append(HOME + "/bin")
from basepaths import loudspeaker_folder
from getconfig import loudspeaker
from getstatus import fs

def borrarSymLinks(audio_folder):
    # borramos los symlink existentes
    for cosa in os.listdir(audio_folder):
        if "drc-" in cosa and ".pcm" in cosa:
            os.remove(audio_folder + cosa)

def nuevosSymLinks(audio_folder):
    # hacemos nuevos symlinks
    for root, dirs, files in os.walk(audio_folder, topdown=False):
        for subdir  in dirs:
            for x in [x for x in os.listdir(os.path.join(root, subdir)) if x.endswith(".pcm")]:
                filtroFullPath = os.path.join(root, subdir, x)
                # print filtroFullPath # DEBUG

                comando = "ln -s '" + filtroFullPath + "' '" \
                          + audio_folder + subdir + "-" + x[0] + ".pcm'"

                #print comando
                os.system(comando)

def comprueba(audio_folder):
    #os.system("ls -lh "+ audio_folder + "drc-*")
    print
    print "(i) para comprobar ejecutar   ls -lh "+ audio_folder + "drc-*"
    print

def main(audio_folder):
    if audio_folder[-1] <> "/":
        audio_folder += "/"
    print
    print u"vamos a crear, para compatibilidad con el script de control, "
    print u"los symlinks 'drc-X-Y' en " + audio_folder
    print u"a partir de los pcm de los subdirectorios 'drc-X' encontrados allí \n"

    raw_input("presiona Ctrl+C para cancelar o Intro para continuar")

    borrarSymLinks(audio_folder)
    nuevosSymLinks(audio_folder)
    comprueba(audio_folder)

if __name__ == '__main__':

    # si se pasan argumentos los atendemos
    if sys.argv[1:]:
        args = sys.argv[1:]

        # si se indica una carpeta de altavoz en particular
        # OjO debe proporcionarse como "lspk/otroAltavoz"
        tmp = [x for x in args if "lspk/" in x]
        if tmp:
            loudspeaker = tmp[0].split("lspk/")[1]

        # se pide ayuda
        tmp = [x for x in args if "-h" in x]
        if tmp:
            print __doc__
            sys.exit(0)

    else:
        print __doc__
        sys.exit(0)


    audio_folder = loudspeaker_folder + loudspeaker + "/" + fs
    main(audio_folder)
